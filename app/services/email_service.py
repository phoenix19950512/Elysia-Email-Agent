import json
import os
from datetime import datetime
from app.auth.graph_auth import GraphAuth
from app.models.schema import EmailMessage
from app.services.openai_service import openai_service
from app.services.supabase_service import supabase_service

class EmailService:
    def __init__(self, graph_auth: GraphAuth):
        self.auth = graph_auth

    async def get_emails(self, folder="inbox", max_count=None):
        """Get emails from a specific folder"""
        params = {
            "$orderby": "receivedDateTime DESC",
            "$select": "id,subject,bodyPreview,from,toRecipients,ccRecipients,receivedDateTime,importance,isRead,hasAttachments"
        }
        if max_count:
            params["$top"] = max_count
        
        endpoint = f"me/mailFolders/{folder}/messages"
        response = await self.auth.make_request("GET", endpoint, params=params)
        
        if response and "value" in response:
            emails = []
            for item in response["value"]:
                sender = item["from"]["emailAddress"]["address"] if "from" in item and "emailAddress" in item["from"] else None
                
                email = EmailMessage(
                    id=item["id"],
                    subject=item["subject"],
                    body=item["bodyPreview"],
                    to_recipients=[r["emailAddress"]["address"] for r in item["toRecipients"]],
                    importance=item["importance"],
                    is_read=item["isRead"],
                    has_attachments=item["hasAttachments"],
                    received_date_time=datetime.fromisoformat(item["receivedDateTime"].replace('Z', '+00:00')),
                    sender=sender
                )
                emails.append(email)
            return emails
        return []

    async def get_email_content(self, email_id):
        """Get full content of a specific email"""
        endpoint = f"me/messages/{email_id}"
        response = await self.auth.make_request("GET", endpoint)
        return response
    
    async def delete_email(self, email_id):
        """Delete an email"""
        endpoint = f"me/messages/{email_id}"
        response = await self.auth.make_request("DELETE", endpoint)
        return response

    # In app/services/email_service.py
    async def get_folders(self):
        """Get all mail folders"""
        try:
            endpoint = f"me/mailFolders"
            params = {
                "$top": 100
            }
            response = await self.auth.make_request("GET", endpoint, params=params)
            
            if response and "value" in response:
                return response.get("value", [])
            return []
        except Exception as e:
            print(f"Error in get_folders: {str(e)}")
            return []


    async def create_folder(self, display_name):
        """Create a new mail folder"""
        endpoint = f"me/mailFolders"
        data = {
            "displayName": display_name
        }
        response = await self.auth.make_request("POST", endpoint, data=data)
        return response

    async def sort_emails(self, folders, emails):
        """Sort emails based on existing folders"""
        results = []

        for email in emails:
            prompt = openai_service.generate_sort_mail_prompt(folders, email.subject, str(email.body))
            messages = [{'role': 'user', 'content': prompt}]
            target_folder = await openai_service.get_openai_response(messages)
            target_folder = target_folder.replace('```', '').replace('"', '').replace("'", '')
            email_id = email.id
            await self.move_email(email_id, target_folder)
            supabase_service.log_activity(self.auth.email, 'sort_email', f"Sorted mail {email_id} to {target_folder}")
            results.append({
                "id": email_id,
                "subject": email.subject,
                "target_folder": target_folder
            })
        return results

    async def move_email(self, email_id, target_folder):
        """Move an email to a specific folder"""
        endpoint = f"me/messages/{email_id}/move"
        data = {
            "destinationId": target_folder
        }
        return await self.auth.make_request("POST", endpoint, data=data)

    async def send_reply(self, email_id, template, send_without_approval=False):
        """Send a reply to an email"""
        # First, get the email to reply to
        email = await self.get_email_content(email_id)
        subject = email.get("subject", "")
        prompt = openai_service.generate_reply_prompt(template, subject, email.get("body", {}).get("content", ""))
        messages = [{'role': 'user', 'content': prompt}]
        response = await openai_service.get_openai_response(messages)
        
        # Create reply
        if send_without_approval:
            # Send without approval
            endpoint = f"me/messages/{email_id}/reply"
            data = {
                "comment": response
            }
            supabase_service.log_activity(self.auth.email, 'send_reply', f"Replied to mail {email_id}")
            return await self.auth.make_request("POST", endpoint, data=data)
        else:
            # Create a draft reply
            recipient = email["from"]["emailAddress"]
            
            endpoint = f"me/messages"
            data = {
                "subject": f"RE: {subject}",
                "body": {
                    "contentType": "HTML",
                    "content": response
                },
                "toRecipients": [
                    {
                        "emailAddress": recipient
                    }
                ]
            }
            supabase_service.log_activity(self.auth.email, 'send_reply', f"Replied to mail {email_id}")
            return await self.auth.make_request("POST", endpoint, data=data)

    async def set_follow_up(self, email_id, reminder_date, note=None):
        """Set a follow-up flag for an email"""
        endpoint = f"me/messages/{email_id}"

        data = {
            "flag": {
                "flagStatus": "flagged",
                "startDateTime": {
                    "dateTime": reminder_date.isoformat(),
                    "timeZone": "UTC"
                },
                "dueDateTime": {
                    "dateTime": reminder_date.isoformat(),
                    "timeZone": "UTC"
                }
            }
        }

        supabase_service.log_activity(self.auth.email, 'set_follow_up', f"Follow up mail {email_id}")
        return await self.auth.make_request("PATCH", endpoint, data=data)


    def get_templates(self):
        """Get email templates from the template file"""
        template_path = os.path.join("app", "templates", "email_templates.json")
        
        if not os.path.exists(template_path):
            # Create default templates if file doesn't exist
            default_templates = [
                {
                    "name": "General Reply",
                    "subject": "RE: {original_subject}",
                    "body": "Thank you for your email. I will review it and get back to you soon.<br><br>Best regards,<br>Elysia Partners"
                },
                {
                    "name": "Meeting Confirmation",
                    "subject": "RE: {original_subject}",
                    "body": "I confirm that I will attend the meeting.<br><br>Best regards,<br>Elysia Partners"
                }
            ]
            
            os.makedirs(os.path.dirname(template_path), exist_ok=True)
            with open(template_path, "w") as f:
                json.dump(default_templates, f, indent=4)
            
            return default_templates
        
        with open(template_path, "r") as f:
            return json.load(f)
