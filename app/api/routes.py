# type: ignore

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Body
from fastapi.responses import JSONResponse
from typing import List, Optional
import json
from datetime import datetime
from app.services.email_service import EmailService
from app.services.meeting_service import MeetingService
from app.services.file_service import FileService
from app.services.ai_service import AIService
from app.models.schema import EmailRule, EmailTemplate, FollowUp
import os
import json

# Add to app/api/routes.py
from app.services.chat_service import ChatService
from app.services.activity_service import ActivityService

router = APIRouter()

# Initialize services
email_service = EmailService()
meeting_service = MeetingService()
file_service = FileService()
ai_service = AIService()

# Email endpoints
@router.get("/emails")
async def get_emails(folder: str = "inbox", max_count: int = 25):
    try:
        emails = email_service.get_emails(folder, max_count)
        return {"emails": [email.dict() for email in emails]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emails/{email_id}")
async def get_email(email_id: str):
    try:
        email = email_service.get_email_content(email_id)
        return email
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add this to your routes.py
@router.get("/test-graph")
async def test_graph_connection():
    """Test Microsoft Graph API connection"""
    try:
        graph_auth = GraphAuth()
        response = graph_auth.make_request("GET", "me")
        return {"status": "connected", "response": response}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# In app/api/routes.py
@router.get("/folders")
async def get_folders():
    try:
        folders = email_service.get_folders()
        return {"folders": folders}
    except Exception as e:
        error_message = str(e)
        print(f"Error in /folders endpoint: {error_message}")
        
        if "401" in error_message:
            raise HTTPException(
                status_code=401, 
                detail="Authentication error with Microsoft Graph API. Please check credentials and permissions."
            )
        else:
            raise HTTPException(status_code=500, detail=error_message)

@router.post("/folders")
async def create_folder(display_name: str = Body(..., embed=True)):
    try:
        folder = email_service.create_folder(display_name)
        return folder
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sort-emails")
async def sort_emails(rules: List[EmailRule]):
    try:
        results = email_service.sort_emails(rules)
        return {"sorted_emails": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reply-email")
async def reply_email(
    email_id: str = Form(...),
    template_name: str = Form(...), 
    send_without_approval: bool = Form(False)
):
    try:
        # Get email content
        email = email_service.get_email_content(email_id)
        
        # Get templates
        templates = email_service.get_templates()
        
        # Find the requested template
        template = next((t for t in templates if t["name"] == template_name), None)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Generate personalized reply using AI
        email_content = email.get("body", {}).get("content", "")
        subject = email.get("subject", "")
        
        customized_reply = ai_service.generate_email_reply(
            email_content, 
            template_name, 
            template["body"]
        )
        
        # Send reply
        result = email_service.send_reply(
            email_id,
            subject,
            customized_reply,
            send_without_approval
        )
        
        return {
            "status": "sent" if send_without_approval else "draft_created",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/set-follow-up")
async def set_follow_up(follow_up: FollowUp):
    try:
        result = email_service.set_follow_up(
            follow_up.email_id,
            follow_up.reminder_date,
            follow_up.note
        )
        return {"status": "follow_up_set", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates")
async def get_templates():
    try:
        templates = email_service.get_templates()
        return {"templates": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Meeting endpoints
@router.get("/meetings")
async def get_meetings(days: int = 7):
    try:
        meetings = meeting_service.get_upcoming_meetings(days)
        return {"meetings": [meeting.__dict__ for meeting in meetings]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/join-meeting")
async def join_meeting(meeting_url: str = Body(..., embed=True)):
    try:
        result = meeting_service.join_meeting(meeting_url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/meeting-notes")
async def save_meeting_notes(
    meeting_id: str = Form(...),
    notes: str = Form(...),
    action_items: str = Form(...)
):
    try:
        # Parse action items from string (comma-separated list)
        action_items_list = [item.strip() for item in action_items.split(",") if item.strip()]
        
        meeting_notes = meeting_service.save_meeting_notes(
            meeting_id,
            notes,
            action_items_list
        )
        
        return {"status": "notes_saved", "meeting_notes": meeting_notes.__dict__}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-meeting-follow-up")
async def send_meeting_follow_up(
    meeting_id: str = Form(...),
    notes: str = Form(...),
    action_items: str = Form(...)
):
    try:
        # Parse action items from string
        action_items_list = [item.strip() for item in action_items.split(",") if item.strip()]
        
        # Save meeting notes
        meeting_notes = meeting_service.save_meeting_notes(
            meeting_id,
            notes,
            action_items_list
        )
        
        # Send follow-up email
        result = meeting_service.send_meeting_follow_up(meeting_id, meeting_notes)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# File processing endpoints
@router.post("/process-file")
async def process_file(file: UploadFile = File(...)):
    try:
        # Save the uploaded file
        file_path = file_service.save_uploaded_file(file)
        
        # Process the file
        result = file_service.process_file(file_path)
        
        # Generate a summary using AI
        if result.extracted_text:
            summary = ai_service.summarize_document(result.extracted_text)
            result.summary = summary
        
        return {"status": "file_processed", "result": result.__dict__}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# AI analysis endpoint
@router.post("/analyze-email")
async def analyze_email(email_id: str = Body(..., embed=True)):
    try:
        # Get email content
        email = email_service.get_email_content(email_id)
        
        # Extract the email body
        email_content = email.get("body", {}).get("content", "")
        
        # Analyze the email
        analysis = ai_service.analyze_email(email_content)
        
        return {"analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Initialize new services
chat_service = ChatService()
activity_service = ActivityService()

# Chat endpoints
@router.post("/chat")
async def chat(user_id: str = Body(...), message: str = Body(...)):
    try:
        response = chat_service.process_message(user_id, message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat-history/{user_id}")
async def get_chat_history(user_id: str):
    try:
        history = chat_service.get_chat_history(user_id)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Activity tracking endpoints
@router.get("/activity-summary/{user_id}")
async def get_activity_summary(user_id: str):
    try:
        summary = activity_service.get_activity_summary(user_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Settings endpoints
@router.get("/settings/{user_id}")
async def get_settings(user_id: str):
    try:
        # Get user settings from a file or database
        settings_path = os.path.join(os.getcwd(), "user_settings", f"{user_id}_settings.json")
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                settings = json.load(f)
        else:
            settings = {
                "email_rules": [],
                "templates": email_service.get_templates(),
                "schedules": []
            }
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings/{user_id}")
async def update_settings(user_id: str, settings: dict = Body(...)):
    try:
        # Save user settings
        os.makedirs(os.path.join(os.getcwd(), "user_settings"), exist_ok=True)
        settings_path = os.path.join(os.getcwd(), "user_settings", f"{user_id}_settings.json")
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=2)
        return {"message": "Settings updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
