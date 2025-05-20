from pydantic import BaseModel, EmailStr
from datetime import datetime

class ReplyTemplateCreate(BaseModel):
    email: EmailStr
    name: str
    subject: str
    body: str
    
class ReplyTemplateRead(ReplyTemplateCreate):
    id: str
    timestamp: datetime
