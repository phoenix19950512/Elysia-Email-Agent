from collections import Counter
from datetime import datetime, timezone
from fastapi import HTTPException
from app.models.follow_up import FollowUpCreate
from app.models.reply_template import ReplyTemplateCreate
from app.models.user import UserCreate
from app.api.supabase import supabase
from app.services.openai_service import openai_service

class SupabaseService:
    def __init__(self):
        pass
    
    def create_user(self, user: UserCreate):
        try:
            existing = supabase.table('users').select('*').eq('email', user.email).execute()
            if existing.data:
                user_data = supabase.table('users').update({
                    'access_token': user.access_token,
                    'refresh_token': user.refresh_token,
                    'timestamp': 'now()',
                }).eq('email', user.email).execute()
            else:
                user_data = supabase.table('users').insert({
                    'email': user.email,
                    'access_token': user.access_token,
                    'refresh_token': user.refresh_token,
                    'timestamp': 'now()',
                    'automation': True,
                    'subscription': 'none'
                }).execute()
                supabase.table('schedules').insert({
                    'user_mail': user.email,
                    'name': 'Reminder - 3 Days',
                    'days': 3,
                    'timestamp': 'now()'
                }).execute()
                supabase.table('reply_templates').insert({
                    'user_mail': user.email,
                    'name': 'General Reply',
                    'subject': 'RE: {original_subject}',
                    'body': "Thanks for your email. I'll get back to you shortly.",
                    'timestamp': 'now()'
                }).execute()

            return user_data.data[0]
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error creating user: {e}")
            raise HTTPException(detail=str(e), status_code=500)
    
    def get_user(self, email: str):
        try:
            user_data = supabase.table('users').select('*').eq('email', email).execute()
            return user_data.data[0] if user_data.data else None
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error get user: {e}")
            raise HTTPException(detail=str(e), status_code=500)
        
    def get_all_users(self):
        try:
            user_data = supabase.table('users').select('*').execute()
            return user_data.data
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error get all users: {e}")
            raise HTTPException(detail=str(e), status_code=500)
    
    def update_subscription(self, email: str, subscription: str):
        try:
            user_data = supabase.table('users').update({
                'subscription': subscription
            }).eq('email', email).execute()
            return user_data.data[0]
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error update user subscription: {e}")
            raise HTTPException(detail=str(e), status_code=500)
    
    def update_access_token(self, email: str, access_token: str):
        try:
            user_data = supabase.table('users').update({
                'access_token': access_token
            }).eq('email', email).execute()
            return user_data.data[0]
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error update user access token: {e}")
            raise HTTPException(detail=str(e), status_code=500)
    
    def delete_user(self, email: str):
        try:
            user = self.get_user(email)
            if not user:
                raise HTTPException(detail="User not found", status_code=404)
            supabase.table('activity_logs').delete().eq('user_mail', email).execute()
            supabase.table('chat_history').delete().eq('user_mail', email).execute()
            supabase.table('reply_templates').delete().eq('user_mail', email).execute()
            supabase.table('schedules').delete().eq('user_mail', email).execute()
            user_data = supabase.table('users').delete().eq('email', email).execute()
            return user_data.data[0]
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error delete user: {e}")
            raise HTTPException(detail=str(e), status_code=500)
    
    def toggle_user_automation(self, email: str, state: bool):
        try:
            user_data = supabase.table('users').update({
                'automation': state
            }).eq('email', email).execute()
            return user_data.data[0]
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error toggle user automation: {e}")
            raise HTTPException(detail=str(e), status_code=500)
    
    def log_activity(self, email: str, activity: str, details: str = ''):
        """Log user activity
        activity: "sort_email" | "send_reply" | "set_follow_up" | "process_file" | "join_meeting"
        """
        try:
            activity_data = supabase.table('activity_logs').insert({
                'user_mail': email,
                'activity': activity,
                'details': details,
                'timestamp': 'now()'
            }).execute()
            return activity_data.data[0]
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error log activity: {e}")
            raise HTTPException(detail=str(e), status_code=500)
    
    def get_activity_summary(self, email: str):
        try:
            summary_data = supabase.table('activity_logs').select('*').eq('user_mail', email).execute()
            activities = summary_data.data
            type_counts = Counter(a["activity"] for a in activities)
            summary = {
                "emails_sorted": type_counts.get("sort_email", 0),
                "replies_sent": type_counts.get("send_reply", 0),
                "follow_ups_set": type_counts.get("set_follow_up", 0),
                "files_processed": type_counts.get("process_file", 0),
                "meetings_joined": type_counts.get("join_meeting", 0)
            }
            return summary
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error get activity summary: {e}")
            raise HTTPException(detail=str(e), status_code=500)
    
    async def get_openai_response(self, email: str, prompt: str):
        try:
            response = await openai_service.process_chat_message(prompt)
            self.save_chat_history(email, "user", prompt)
            self.save_chat_history(email, "ai", response)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(detail=str(e), status_code=500)

    def save_chat_history(self, email: str, sender: str, message: str):
        try:
            chat_data = supabase.table('chat_history').insert({
                'user_mail': email,
                'sender': sender,
                'message': message,
                'timestamp': 'now()'
            }).execute()
            return chat_data.data[0]
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error save chat history: {e}")
            raise HTTPException(detail=str(e), status_code=500)
    
    def get_chat_history(self, email: str):
        try:
            chat_data = supabase.table('chat_history').select('*').eq('user_mail', email).execute()
            return chat_data.data
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error get chat history: {e}")
            raise HTTPException(detail=str(e), status_code=500)
        
    def create_reply_template(self, template: ReplyTemplateCreate):
        try:
            template_data = supabase.table('reply_templates').insert({
                'user_mail': template.email,
                'name': template.name,
                'subject': template.subject,
                'body': template.body,
                'timestamp': 'now()'
            }).execute()
            return template_data.data[0]
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error create reply template: {e}")
            raise HTTPException(detail=str(e), status_code=500)

    def get_reply_templates(self, email: str):
        try:
            templates_data = supabase.table('reply_templates').select('*').eq('user_mail', email).execute()
            return templates_data.data
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error get reply templates: {e}")
            raise HTTPException(detail=str(e), status_code=500)
    
    def update_reply_template(self, template_id: str, template: ReplyTemplateCreate):
        try:
            template_data = supabase.table('reply_templates').update({
                'name': template.name,
                'subject': template.subject,
                'body': template.body,
                'timestamp': 'now()'
            }).eq('id', template_id).execute()
            return template_data.data[0]
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error update reply template: {e}")
            raise HTTPException(detail=str(e), status_code=500)
    
    def delete_reply_template(self, template_id: str):
        try:
            template_data = supabase.table('reply_templates').delete().eq('id', template_id).execute()
            return template_data.data[0]
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error delete reply template: {e}")
            raise HTTPException(detail=str(e), status_code=500)

    def create_schedule(self, schedule: FollowUpCreate):
        try:
            schedule_data = supabase.table('schedules').insert({
                'user_mail': schedule.email,
                'name': schedule.name,
                'days': schedule.days,
                'timestamp': 'now()'
            }).execute()
            return schedule_data.data[0]
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error create schedule: {e}")
            raise HTTPException(detail=str(e), status_code=500)
    
    def get_schedules(self, email: str):
        try:
            schedules_data = supabase.table('schedules').select('*').eq('user_mail', email).execute()
            return schedules_data.data
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error get schedules: {e}")
            raise HTTPException(detail=str(e), status_code=500)
    
    def update_schedule(self, schedule_id: str, schedule: FollowUpCreate):
        try:
            schedule_data = supabase.table('schedules').update({
                'name': schedule.name,
                'days': schedule.days,
                'timestamp': 'now()'
            }).eq('id', schedule_id).execute()
            return schedule_data.data[0]
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error update schedule: {e}")
            raise HTTPException(detail=str(e), status_code=500)
    
    def delete_schedule(self, id: str):
        try:
            schedule_data = supabase.table('schedules').delete().eq('id', id).execute()
            return schedule_data.data[0]
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error delete schedule: {e}")
            raise HTTPException(detail=str(e), status_code=500)

supabase_service = SupabaseService()
