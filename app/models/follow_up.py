from pydantic import BaseModel, EmailStr
from datetime import datetime

class FollowUpCreate(BaseModel):
    email: EmailStr
    name: str
    days: int
    
class FollowUpRead(FollowUpCreate):
    id: str
    timestamp: datetime
