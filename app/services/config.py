# type: ignore

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Microsoft Graph API settings
MS_CLIENT_ID = os.getenv("MS_CLIENT_ID")
MS_CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET")
MS_TENANT_ID = os.getenv("MS_TENANT_ID")
MS_REDIRECT_URI = os.getenv("MS_REDIRECT_URI")
USER_EMAIL = os.getenv("USER_EMAIL")

GRAPH_SCOPES = ["https://graph.microsoft.com/.default"]

# Groq API settings
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
