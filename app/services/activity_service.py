# app/services/activity_service.py
import json
import os
from datetime import datetime

class ActivityService:
    def __init__(self):
        self.activity_dir = os.path.join(os.getcwd(), "activity_logs")
        
        # Create activity directory if it doesn't exist
        if not os.path.exists(self.activity_dir):
            os.makedirs(self.activity_dir)
    
    def log_activity(self, user_id, activity_type, details=None):
        """Log a user activity"""
        timestamp = datetime.now().isoformat()
        log_file = os.path.join(self.activity_dir, f"{user_id}_activity.json")
        
        # Load existing logs or create new
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                activities = json.load(f)
        else:
            activities = []
        
        # Add new activity
        activities.append({
            "timestamp": timestamp,
            "type": activity_type,
            "details": details or {}
        })
        
        # Save updated activities
        with open(log_file, 'w') as f:
            json.dump(activities, f, indent=2)
    
    def get_activity_summary(self, user_id):
        """Get summary of user activities"""
        log_file = os.path.join(self.activity_dir, f"{user_id}_activity.json")
        
        if not os.path.exists(log_file):
            return {
                "emails_sorted": 0,
                "replies_sent": 0,
                "follow_ups_set": 0,
                "files_processed": 0,
                "meetings_joined": 0
            }
        
        with open(log_file, 'r') as f:
            activities = json.load(f)
        
        # Count activities by type
        summary = {
            "emails_sorted": sum(1 for a in activities if a["type"] == "sort_email"),
            "replies_sent": sum(1 for a in activities if a["type"] == "send_reply"),
            "follow_ups_set": sum(1 for a in activities if a["type"] == "set_follow_up"),
            "files_processed": sum(1 for a in activities if a["type"] == "process_file"),
            "meetings_joined": sum(1 for a in activities if a["type"] == "join_meeting")
        }
        
        return summary
