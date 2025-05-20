from fastapi import HTTPException
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_USERNAME, SUPABASE_PASSWORD

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
def sign_in_supabase():
    user = supabase.auth.sign_in_with_password({"email": SUPABASE_USERNAME, "password": SUPABASE_PASSWORD})
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user.session.access_token

def get_supabase_user(token: str):
    user = supabase.auth.get_user(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

token = sign_in_supabase()
get_supabase_user(token)
