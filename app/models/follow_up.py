from pydantic import BaseModel, EmailStr
from datetime import datetime

class FollowUpCreate(BaseModel):
    user_mail: EmailStr
    name: str
    days: int
    
class FollowUpRead(FollowUpCreate):
    id: str
    timestamp: datetime
