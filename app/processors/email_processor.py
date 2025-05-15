import asyncio
import json
import os
from app.auth.graph_auth import graph_auth
from app.services.email_service import email_service

class EmailProcessor:
    def __init__(self) -> None:
        self.running = False
        self.check_interval = int(os.getenv("EMAIL_CHECK_INTERVAL", "300"))
        self.ms_client = graph_auth
    
    async def start(self):
        if self.running:
            return
        
        self.running = True
        print("Starting email processor")
        while self.running:
            folders = await email_service.get_folders()
            if not folders:
                continue
            folder = next((f for f in folders if f["displayName"].lower() == 'inbox'), None)
            if not folder:
                continue
            try:
                # Get a new database session for this iteration
                settings_path = os.path.join(os.getcwd(), "user_settings", "user123_settings.json")
                if os.path.exists(settings_path):
                    with open(settings_path, 'r') as f:
                        settings = json.load(f)
                        turn_on = settings.get("turn_on", True)
                        email_rules = settings.get("email_rules", [])
                        followup_schedules = settings.get("schedules", [])
                else:
                    email_rules = []
                    followup_schedules = []
                    turn_on = True
                
                if turn_on == True:
                    emails = await email_service.get_emails(folder['id'])
                    for email in emails:
                        await email_service.send_reply(
                            email_id=email['id'],
                            subject=email['subject'],
                            body=email['body']
                        )
                        for schedule in followup_schedules:
                            await email_service.set_follow_up(
                                email_id=email['id'],
                                reminder_date=schedule.get("days", 3)
                            )
                    await email_service.sort_emails(email_rules)

            except Exception as e:
                print(f"Error in email processor: {str(e)}")
        
            await asyncio.sleep(self.check_interval)
        
    def stop(self):
        print("Stopping email processor")
        self.running = False
