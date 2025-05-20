# type: ignore

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Microsoft Graph API settings
MS_CLIENT_ID = os.getenv("MS_CLIENT_ID")
MS_TENANT_ID = os.getenv("MS_TENANT_ID")
MS_REDIRECT_URI = os.getenv("MS_REDIRECT_URI")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_USERNAME = os.getenv("SUPABASE_USERNAME")
SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD")
ACCESS_TOKEN_EXPIRE_MINUTES = 129600 # 90 days
ALGORITHM = "HS512"
SECRET_KEY = os.getenv("SECRET_KEY")
