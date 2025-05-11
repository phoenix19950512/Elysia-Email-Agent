# app/services/chat_service.py
import json
import os
from datetime import datetime
from app.services.ai_service import AIService

class ChatService:
    def __init__(self):
        self.ai_service = AIService()
        self.chat_history_dir = os.path.join(os.getcwd(), "chat_history")
        
        # Create chat history directory if it doesn't exist
        if not os.path.exists(self.chat_history_dir):
            os.makedirs(self.chat_history_dir)
    
    def process_message(self, user_id, message):
        """Process a user message and generate a response"""
        # Save to chat history
        self.save_to_history(user_id, "user", message)
        
        # Process with AI
        response = self.ai_service.process_chat_message(message)
        
        # Save AI response to history
        self.save_to_history(user_id, "ai", response)
        
        return response
    
    def save_to_history(self, user_id, sender, message):
        """Save a message to the chat history"""
        timestamp = datetime.now().isoformat()
        history_file = os.path.join(self.chat_history_dir, f"{user_id}_history.json")
        
        # Load existing history or create new
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        # Add new message
        history.append({
            "timestamp": timestamp,
            "sender": sender,
            "message": message
        })
        
        # Save updated history
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def get_chat_history(self, user_id):
        """Get chat history for a user"""
        history_file = os.path.join(self.chat_history_dir, f"{user_id}_history.json")
        
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                return json.load(f)
        return []
