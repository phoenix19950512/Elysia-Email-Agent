from openai import AsyncOpenAI
from config import OPENAI_API_KEY

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

class OpenAIService:
    def __init__(self) -> None:
        pass

    async def get_openai_response(self, messages, model='gpt-3.5-turbo'):
        res = await openai_client.responses.create(input=messages, model=model)
        return res.output_text
    
    async def analyze_email(self, email_content):
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
        
        messages = [{'role': 'user', 'content': prompt}]
        response = await self.get_openai_response(messages)
        return response

    async def process_meeting_notes(self, transcript):
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
        
        messages = [{'role': 'user', 'content': prompt}]
        response = await self.get_openai_response(messages)
        return response
    
    async def summarize_document(self, text):
        """Summarize document content"""
        # If text is too long, truncate it to fit within token limits
        if len(text) > 8000:
            text = text[:8000] + "..."
            
        prompt = f"""
        Please provide a concise summary of the following document:
        
        {text}
        
        Key points to include in the summary:
        """
        
        messages = [{'role': 'user', 'content': prompt}]
        response = await self.get_openai_response(messages)
        return response

    # Add to app/services/ai_service.py
    async def process_chat_message(self, message):
        """Process a chat message and generate a response"""
        prompt = f"""
        You are an Email AI Assistant for Elysia Partners. Respond to the following query 
        in a helpful, professional manner. If the query is about email management, 
        sorting, or scheduling, provide specific guidance.
        
        User message: {message}
        
        Your response:
        """
        
        messages = [{'role': 'user', 'content': prompt}]
        response = await self.get_openai_response(messages)
        return response

    def generate_reply_prompt(self, template, email_subject: str, email_content: str):
        return f"""
        You need to customize the following email template to create a personalized reply
        to the email content below. Maintain a professional tone.
        Don't select default folders of Microsoft Outlook.
        Don't include single or double quota in the result.
        
        Template name: {template.get("name", "(No Name)")}
        Template subject: {template.get("subject", "(No subject)")}
        Template content:
        ```
        {template.get("body", "(No body)")}
        ```
        
        Original email subject: {email_subject}
        Original email content:
        ```
        {email_content}
        ```

        Generate a personalized reply based on the template.
        Don't include your explanations so that I can send your response to the recipient without any processing."""
    
    def generate_sort_mail_prompt(self, folders: list, email_subject: str, email_content: str):
        return f"""
        You need to return only target folder's id according to the email.
        Select the target folder only in these folders.
        
        Folders:
        ```
        {folders}
        ```
        
        Original email subject: {email_subject}
        Original email content:
        ```
        {email_content}
        ```
        
        Return only target folder's id"""

openai_service = OpenAIService()
