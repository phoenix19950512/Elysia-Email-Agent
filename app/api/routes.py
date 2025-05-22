# type: ignore

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Body
from pydantic import BaseModel

from app.api.auth import get_current_graph, create_jwt_token
from app.auth.graph_auth import GraphAuth
from app.services.email_service import EmailService
from app.services.meeting_service import MeetingService
from app.services.file_service import FileService
from app.services.openai_service import openai_service
from app.services.supabase_service import supabase_service
from app.models.follow_up import FollowUpCreate
from app.models.reply_template import ReplyTemplateCreate
from app.models.user import UserCreate

class AutomationToggle(BaseModel):
    state: bool

class SubscriptionUpdate(BaseModel):
    subscription: str

class FollowUp(BaseModel):
    email_id: str
    reminder_date: int
    note: str

router = APIRouter()

# Initialize services
file_service = FileService()

@router.post("/signin")
async def signin(user: UserCreate):
    graph_auth = GraphAuth(user.access_token, user.refresh_token)
    is_valid_token = await graph_auth.validate_token(user.access_token)
    if not is_valid_token:
        raise HTTPException(status_code=401, detail="Invalid access token")
    data = {
        "email": user.email,
        "access_token": user.access_token,
        "refresh_token": user.refresh_token,
    }
    access_token = create_jwt_token(data=data)
    supabase_service.create_user(user)
    return { "access_token": access_token }

@router.post("/verify-token")
async def verify_token(graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        return {"message": "Token is valid"}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

# Email endpoints
@router.get("/emails")
async def get_emails(
    folder: str = "inbox",
    max_count: int = 25,
    graph_auth: GraphAuth = Depends(get_current_graph)
):
    try:
        email_service = EmailService(graph_auth)
        emails = await email_service.get_emails(folder, max_count)
        return emails
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emails/{email_id}")
async def get_email(email_id: str, graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        email_service = EmailService(graph_auth)
        email = await email_service.get_email_content(email_id)
        return email
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/draft-emails")
async def get_draft_emails(
    max_count: int = 25,
    graph_auth: GraphAuth = Depends(get_current_graph)
):
    try:
        email_service = EmailService(graph_auth)
        folders = await email_service.get_folders()
        drafts_folder = next((folder for folder in folders if folder["displayName"] == "Drafts"), None)
        if not drafts_folder:
            raise HTTPException(status_code=404, detail="Drafts folder not found")
        folder_id = drafts_folder["id"]
        emails = await email_service.get_emails(folder_id, max_count)
        return emails
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/emails/{email_id}")
async def delete_email(email_id: str, graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        email_service = EmailService(graph_auth)
        await email_service.delete_email(email_id)
        return {"message": "Email deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inbox-count")
async def count_inbox_mails(graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        email_service = EmailService(graph_auth)
        emails = await email_service.get_emails()
        return len(emails)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/draft-count")
async def count_draft_mails(graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        email_service = EmailService(graph_auth)
        emails = await email_service.get_emails(folder="drafts")
        return len(emails)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add this to your routes.py
@router.get("/test-graph")
async def test_graph_connection(graph_auth: GraphAuth = Depends(get_current_graph)):
    """Test Microsoft Graph API connection"""
    try:
        response = await graph_auth.make_request("GET", "me")
        return {"status": "connected", "response": response}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# In app/api/routes.py
@router.get("/folders")
async def get_folders(graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        email_service = EmailService(graph_auth)
        folders = await email_service.get_folders()
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
async def create_folder(
    display_name: str = Body(..., embed=True),
    graph_auth: GraphAuth = Depends(get_current_graph)
):
    try:
        email_service = EmailService(graph_auth)
        folder = await email_service.create_folder(display_name)
        return folder
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @router.post("/sort-emails")
# async def sort_emails(rules: List[EmailRule]):
#     try:
#         results = await email_service.sort_emails(rules)
#         return {"sorted_emails": results}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.post("/reply-email")
async def reply_email(
    email_id: str = Form(...),
    template_name: str = Form(...), 
    send_without_approval: bool = Form(False),
    graph_auth: GraphAuth = Depends(get_current_graph)
):
    try:
        templates = supabase_service.get_reply_templates(graph_auth.email)
        email_service = EmailService(graph_auth)
        
        # Find the requested template
        template = next((t for t in templates if t["name"] == template_name), None)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Send reply
        result = await email_service.send_reply(
            email_id,
            template,
            send_without_approval
        )
        
        return {
            "status": "sent" if send_without_approval else "draft_created",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/set-follow-up")
async def set_follow_up(follow_up: FollowUp, graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        email_service = EmailService(graph_auth)
        result = await email_service.set_follow_up(
            follow_up.email_id,
            follow_up.reminder_date,
            follow_up.note
        )
        return {"status": "follow_up_set", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Meeting endpoints
@router.get("/meetings")
async def get_meetings(days: int = 7, graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        meeting_service = MeetingService(graph_auth)
        meetings = await meeting_service.get_upcoming_meetings(days)
        return {"meetings": [meeting.__dict__ for meeting in meetings]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/join-meeting")
async def join_meeting(meeting_url: str = Body(..., embed=True), graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        meeting_service = MeetingService(graph_auth)
        result = meeting_service.join_meeting(meeting_url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/meeting-notes")
async def save_meeting_notes(
    meeting_id: str = Form(...),
    notes: str = Form(...),
    action_items: str = Form(...),
    graph_auth: GraphAuth = Depends(get_current_graph)
):
    try:
        meeting_service = MeetingService(graph_auth)
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
    action_items: str = Form(...),
    graph_auth: GraphAuth = Depends(get_current_graph)
):
    try:
        meeting_service = MeetingService(graph_auth)
        # Parse action items from string
        action_items_list = [item.strip() for item in action_items.split(",") if item.strip()]
        
        # Save meeting notes
        meeting_notes = meeting_service.save_meeting_notes(
            meeting_id,
            notes,
            action_items_list
        )
        
        # Send follow-up email
        result = await meeting_service.send_meeting_follow_up(meeting_id, meeting_notes)
        
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
            summary = await openai_service.summarize_document(result.extracted_text)
            result.summary = summary
        
        return {"status": "file_processed", "result": result.__dict__}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# AI analysis endpoint
@router.post("/analyze-email")
async def analyze_email(email_id: str = Body(..., embed=True), graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        email_service = EmailService(graph_auth)
        # Get email content
        email = await email_service.get_email_content(email_id)
        
        # Extract the email body
        email_content = email.get("body", {}).get("content", "")
        
        # Analyze the email
        analysis = await openai_service.analyze_email(email_content)
        
        return {"analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Chat endpoints
@router.post("/chat")
async def chat(message: str = Body(...), graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        email = graph_auth.email
        response = await supabase_service.get_openai_response(email, message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat-history")
async def get_chat_history(graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        email = graph_auth.email
        history = supabase_service.get_chat_history(email)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Activity tracking endpoints
@router.get("/activity-summary")
async def get_activity_summary(graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        email = graph_auth.email
        summary = supabase_service.get_activity_summary(email)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Settings endpoints
@router.get("/schedules")
async def get_schedules(graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        email = graph_auth.email
        schedules = supabase_service.get_schedules(email)
        return schedules
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schedules")
async def add_schedule(schedule: FollowUpCreate, graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        new_schedule = supabase_service.create_schedule(schedule)
        return new_schedule
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/schedules/{schedule_id}")
async def update_schedule(schedule_id: str, schedule: FollowUpCreate, graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        updated_schedule = supabase_service.update_schedule(schedule_id, schedule)
        return {"message": "Schedule updated successfully", "schedule": updated_schedule}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str, graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        supabase_service.delete_schedule(schedule_id)
        return {"message": "Schedule deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates")
async def get_templates(graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        templates = supabase_service.get_reply_templates(graph_auth.email)
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/templates")
async def create_template(template: ReplyTemplateCreate, graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        new_template = supabase_service.create_reply_template(template)
        return new_template
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/templates/{template_id}")
async def update_template(template_id: str, template: ReplyTemplateCreate, graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        updated_template = supabase_service.update_reply_template(template_id, template)
        return {"message": "Template updated successfully", "template": updated_template}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/templates/{template_id}")
async def delete_template(template_id: str, graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        supabase_service.delete_reply_template(template_id)
        return {"message": "Template deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/toggle-automation")
async def toggle(toggle_data: AutomationToggle, graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        supabase_service.toggle_user_automation(graph_auth.email, toggle_data.state)
        return {"message": "Automation toggled successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/subscription")
async def update_subscription(subscription_data: SubscriptionUpdate, graph_auth: GraphAuth = Depends(get_current_graph)):
    try:
        supabase_service.update_subscription(graph_auth.email, subscription_data.subscription)
        return {"message": "Subscription updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
