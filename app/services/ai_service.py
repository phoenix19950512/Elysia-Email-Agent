# type: ignore

import os
import groq
from config import GROQ_API_KEY

class AIService:
    def __init__(self):
        self.client = groq.Client(api_key=GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"
    
    def analyze_email(self, email_content):
        """Analyze email content and suggest actions"""
        prompt = f"""
        Please analyze the following email content and:
        1. Identify the main topic/purpose
        2. Rate the urgency (low, medium, high)
        3. Suggest an appropriate action or response
        
        Email Content:
        {email_content}
        
        Your analysis:
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.1
        )
        
        return response.choices[0].message.content
    
    def generate_email_reply(self, email_content, template_name, template_content):
        """Generate a personalized email reply based on a template"""
        prompt = f"""
        You need to customize the following email template to create a personalized reply
        to the email content below. Maintain a professional tone.
        
        Template name: {template_name}
        Template content: {template_content}
        
        Original email content:
        {email_content}
        
        Generate a personalized reply based on the template:
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    def process_meeting_notes(self, transcript):
        """Process meeting transcript and generate structured notes"""
        prompt = f"""
        Please analyze the following meeting transcript and:
        1. Provide a concise summary of the key points discussed
        2. List specific action items with assigned persons if mentioned
        3. Format the output in a structured way suitable for a follow-up email
        
        Meeting transcript:
        {transcript}
        
        Your structured meeting notes:
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.1
        )
        
        return response.choices[0].message.content
    
    def summarize_document(self, text):
        """Summarize document content"""
        # If text is too long, truncate it to fit within token limits
        if len(text) > 8000:
            text = text[:8000] + "..."
            
        prompt = f"""
        Please provide a concise summary of the following document:
        
        {text}
        
        Key points to include in the summary:
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.1
        )
        
        return response.choices[0].message.content

    # Add to app/services/ai_service.py
    def process_chat_message(self, message):
        """Process a chat message and generate a response"""
        prompt = f"""
        You are an Email AI Assistant for Elysia Partners. Respond to the following query 
        in a helpful, professional manner. If the query is about email management, 
        sorting, or scheduling, provide specific guidance.
        
        User message: {message}
        
        Your response:
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3
        )
        
        return response.choices[0].message.content
