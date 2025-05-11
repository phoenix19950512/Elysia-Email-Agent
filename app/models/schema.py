# type: ignore

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class EmailRule(BaseModel):
    field: str  # e.g., "subject", "from", "body"
    value: str  # The value to match
    target_folder: str  # The target folder to move messages to

class EmailTemplate(BaseModel):
    name: str
    subject: str
    body: str

class EmailMessage(BaseModel):
    id: Optional[str] = None
    subject: str
    body: str
    to_recipients: List[str]
    cc_recipients: Optional[List[str]] = []
    importance: Optional[str] = "normal"
    has_attachments: Optional[bool] = False
    is_read: Optional[bool] = False
    received_date_time: Optional[datetime] = None
    sender: Optional[str] = None
    
class FollowUp(BaseModel):
    email_id: str
    reminder_date: datetime
    note: Optional[str] = None
    
class MeetingDetails(BaseModel):
    subject: str
    start_time: datetime
    end_time: datetime
    attendees: List[str]
    body: Optional[str] = None
    online_meeting_url: Optional[str] = None
    
class MeetingNotes(BaseModel):
    meeting_id: str
    notes: str
    action_items: List[str]
    
class FileProcessingRequest(BaseModel):
    file_path: str
    file_type: str  # e.g., "pdf", "image", "text"
    
class FileProcessingResult(BaseModel):
    extracted_text: Optional[str] = None
    summary: Optional[str] = None
    keywords: Optional[List[str]] = None
