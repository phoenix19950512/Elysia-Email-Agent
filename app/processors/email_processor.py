import asyncio
import os
import random
from datetime import datetime, timezone, timedelta
from app.auth.graph_auth import GraphAuth
from app.services.email_service import EmailService
from app.services.supabase_service import supabase_service

class EmailProcessor:
    def __init__(self) -> None:
        self.running = False
        self.check_interval = int(os.getenv("EMAIL_CHECK_INTERVAL", "10"))
    
    async def start(self):
        if self.running:
            return
        
        self.running = True
        print("Starting email processor")
        while self.running:
            users = supabase_service.get_all_users()
            if not users:
                print('No users')
                await asyncio.sleep(self.check_interval)
                continue

            for user in users:
                try:
                    email = user["email"]
                    access_token = user["access_token"]
                    refresh_token = user["refresh_token"]
                    settings_on = user["automation"]
                    if not settings_on:
                        print('Automation is off')
                        continue
                    graph_auth = GraphAuth(user["email"], access_token, refresh_token)
                    email_service = EmailService(graph_auth)
                    folders = await email_service.get_folders()
                    if not folders:
                        print('No folders')
                        continue
                    folder = next((f for f in folders if f["displayName"].lower() == 'inbox'), None)
                    if not folder:
                        print('No inbox folder')
                        continue

                    followup_schedules = supabase_service.get_schedules(email)
                    templates = supabase_service.get_reply_templates(email)
                    emails = await email_service.get_emails(folder["id"])
                    print(f"{len(emails)} emails found.")
                    for email in emails:
                        if email.is_read:
                            continue
                        try:
                            print("Replying email")
                            await email_service.send_reply(
                                email_id=email.id,
                                template=templates[random.randint(0, len(templates) - 1)],
                                send_without_approval=False
                            )
                        except Exception as e:
                            print(e)
                        try:
                            print("Setting flag")
                            for schedule in followup_schedules:
                                days = schedule["days"]
                                reminder_date = datetime.now(timezone.utc) + timedelta(days=days)
                                await email_service.set_follow_up(
                                    email_id=email.id,
                                    reminder_date=reminder_date
                                )
                        except Exception as e:
                            print(e)

                    print("Sorting emails")
                    try:
                        await email_service.sort_emails(folders, emails)
                    except Exception as e:
                        print(e)

                    del emails
                    del graph_auth
                    del email_service

                except Exception as e:
                    print(f"Error processing user {email}: {e}")
                    continue

            del users
            await asyncio.sleep(self.check_interval)
        
    def stop(self):
        print("Stopping email processor")
        self.running = False

email_processor = EmailProcessor()
