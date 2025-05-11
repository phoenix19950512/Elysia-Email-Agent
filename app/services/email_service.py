import json
import os
from datetime import datetime
from app.auth.graph_auth import GraphAuth
from app.models.schema import EmailRule, EmailMessage
from config import USER_EMAIL

class EmailService:
    def __init__(self):
        self.auth = GraphAuth()
        self.user_email = USER_EMAIL

    def get_emails(self, folder="inbox", max_count=25):
        """Get emails from a specific folder"""
        params = {
            "$top": max_count,
            "$orderby": "receivedDateTime DESC",
            "$select": "id,subject,bodyPreview,from,toRecipients,ccRecipients,receivedDateTime,importance,isRead,hasAttachments"
        }
        
        endpoint = f"me/mailFolders/{folder}/messages"
        # endpoint = f"users/{self.user_email}/mailFolders/{folder}/messages"
        response = self.auth.make_request("GET", endpoint, params=params)
        
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

    def get_email_content(self, email_id):
        """Get full content of a specific email"""
        endpoint = f"me/messages/{email_id}"
        # endpoint = f"users/{self.user_email}/messages/{email_id}"
        response = self.auth.make_request("GET", endpoint)
        return response

    # In app/services/email_service.py
    def get_folders(self):
        """Get all mail folders"""
        try:
            endpoint = f"me/mailFolders"
            # endpoint = f"users/{self.user_email}/mailFolders"
            params = {
                "$top": 100  
            }
            response = self.auth.make_request("GET", endpoint, params=params)
            print(f"Folders response: {response}") 
            
            if response and "value" in response:
                return response.get("value", [])
            return []
        except Exception as e:
            print(f"Error in get_folders: {str(e)}")
            return []


    def create_folder(self, display_name):
        """Create a new mail folder"""
        endpoint = f"me/mailFolders"
        # endpoint = f"users/{self.user_email}/mailFolders"
        data = {
            "displayName": display_name
        }
        response = self.auth.make_request("POST", endpoint, data=data)
        return response

    def sort_emails(self, rules):
        """Sort emails based on defined rules"""
        results = []
        
        for rule in rules:
            # Get emails matching the rule
            field = rule.field
            value = rule.value
            
            # Build query based on field
            query = None
            if field == "subject":
                query = f"subject:'{value}'"
            elif field == "from":
                query = f"from:'{value}'"
            elif field == "body":
                # Body search is limited in Microsoft Graph, so we'll retrieve and filter afterward
                query = ""
            
            # Get matching emails
            params = {
                "$search: '{value}'"
                # "$search": query,
                "$top": 50,
                "$select": "id,subject,bodyPreview"
            }
            
            endpoint = f"me/mailFolders/inbox/messages"
            # endpoint = f"users/{self.user_email}/mailFolders/inbox/messages"
            response = self.auth.make_request("GET", endpoint, params=params)
            
            if response and "value" in response:
                # For body search, filter the results
                if field == "body":
                    filtered_emails = [email for email in response["value"] 
                                      if value.lower() in email["bodyPreview"].lower()]
                    emails_to_move = filtered_emails
                else:
                    emails_to_move = response["value"]
                
                # Move each email to the target folder
                for email in emails_to_move:
                    self.move_email(email["id"], rule.target_folder)
                    results.append({
                        "id": email["id"],
                        "subject": email["subject"],
                        "target_folder": rule.target_folder
                    })
                    
        return results

    def move_email(self, email_id, target_folder):
        """Move an email to a specific folder"""
        endpoint = f"me/messages/{email_id}/move"
        # endpoint = f"users/{self.user_email}/messages/{email_id}/move"
        data = {
            "destinationId": target_folder
        }
        return self.auth.make_request("POST", endpoint, data=data)

    def send_reply(self, email_id, subject, body, send_without_approval=False):
        """Send a reply to an email"""
        # First, get the email to reply to
        email = self.get_email_content(email_id)
        
        # Create reply
        if send_without_approval:
            # Send without approval
            endpoint = f"me/messages/{email_id}/reply"
            # endpoint = f"users/{self.user_email}/messages/{email_id}/reply"
            data = {
                "comment": body
            }
            return self.auth.make_request("POST", endpoint, data=data)
        else:
            # Create a draft reply
            recipient = email["from"]["emailAddress"]
            
            endpoint = f"me/messages"
            # endpoint = f"users/{self.user_email}/messages"
            data = {
                "subject": f"RE: {subject}",
                "body": {
                    "contentType": "HTML",
                    "content": body
                },
                "toRecipients": [
                    {
                        "emailAddress": recipient
                    }
                ]
            }
            return self.auth.make_request("POST", endpoint, data=data)

    def set_follow_up(self, email_id, reminder_date, note=None):
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

        print(f"🔔 Setting follow-up for: {email_id}")
        print(f"📅 Reminder datetime: {reminder_date.isoformat()}")
        print(f"📦 Payload: {data}")

        return self.auth.make_request("PATCH", endpoint, data=data)


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
