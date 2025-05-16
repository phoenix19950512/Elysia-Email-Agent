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
USER_PASS = os.getenv("USER_PASS")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# # Graph API scopes
# GRAPH_SCOPES = [
#     "Mail.ReadWrite",
#     "Mail.Send",
#     "MailboxSettings.ReadWrite",
#     "Calendars.ReadWrite",
#     "Files.ReadWrite",
#     "User.Read"
# ]

GRAPH_SCOPES = ["https://graph.microsoft.com/.default"]

# Groq API settings
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
