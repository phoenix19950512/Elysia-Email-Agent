from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    access_token: str
    refresh_token: str
    
class UserRead(UserCreate):
    id: str
    timestamp: datetime
    subscription: str
