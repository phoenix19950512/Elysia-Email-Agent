from pydantic import BaseModel, EmailStr
from datetime import datetime

class ReplyTemplateCreate(BaseModel):
    user_mail: EmailStr
    name: str
    subject: str
    body: str
    
class ReplyTemplateRead(ReplyTemplateCreate):
    id: str
    timestamp: datetime
