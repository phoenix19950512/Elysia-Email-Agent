import asyncio
import json
import os
import random
from datetime import datetime, timezone, timedelta
from app.services.email_service import email_service

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
            folders = await email_service.get_folders()
            if not folders:
                print('No folders')
                await asyncio.sleep(self.check_interval)
                continue
            folder = next((f for f in folders if f["displayName"].lower() == 'inbox'), None)
            if not folder:
                print('No inbox folder')
                await asyncio.sleep(self.check_interval)
                continue
            try:
                # Get a new database session for this iteration
                print('Fetching settings file')
                settings_path = os.path.join(os.getcwd(), "user_settings", "user123_settings.json")
                if os.path.exists(settings_path):
                    with open(settings_path, 'r') as f:
                        settings = json.load(f)
                        turn_on = settings.get("turn_on", True)
                        email_rules = settings.get("email_rules", [])
                        followup_schedules = settings.get("schedules", [])
                        templates = settings.get("templates", [])
                else:
                    email_rules = []
                    followup_schedules = []
                    templates = []
                    turn_on = True
                
                if turn_on == True:
                    emails = await email_service.get_emails(folder['id'])
                    print(f"{len(emails)} emails found.")
                    for email in emails:
                        try:
                            print("Replying email")
                            await email_service.send_reply(
                                email_id=email.id,
                                subject=email.subject,
                                body=templates[random.randint(0, len(templates) - 1)].get("body", ""),
                                send_without_approval=True
                            )
                        except Exception as e:
                            print(e)
                        try:
                            print("Setting flag")
                            for schedule in followup_schedules:
                                days = schedule.get('days', 3)
                                reminder_date = datetime.now(timezone.utc) + timedelta(days=days)
                                await email_service.set_follow_up(
                                    email_id=email.id,
                                    reminder_date=reminder_date
                                )
                        except Exception as e:
                            print(e)
                    print("Sorting emails")
                    try:
                        await email_service.sort_emails(email_rules)
                    except Exception as e:
                        print(e)
                else:
                    print("Setting is turned off")

            except Exception as e:
                print(f"Error in email processor: {str(e)}")
        
            await asyncio.sleep(self.check_interval)
        
    def stop(self):
        print("Stopping email processor")
        self.running = False

email_processor = EmailProcessor()
