import httpx
import msal
from fastapi import HTTPException
from config import MS_CLIENT_ID, MS_TENANT_ID
from app.services.supabase_service import supabase_service

class GraphAuth:
    def __init__(self, email: str, token: str, refresh_token: str = None):
        self.authority = f"https://login.microsoftonline.com/{MS_TENANT_ID or 'consumers'}"
        self.scopes = [
            "Mail.ReadWrite",
            "Mail.Send",
            "MailboxSettings.ReadWrite",
            "Calendars.ReadWrite",
            "Files.ReadWrite",
            "User.Read"
        ]
        self.refresh_token = refresh_token
        self.token = token
        self.email = email
        self.app = msal.PublicClientApplication(MS_CLIENT_ID, authority=self.authority)

    async def validate_token(self, token: str):
        if not token:
            raise HTTPException(detail="❌ Token is missing", status_code=404)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {token}"}
            )
        if response.status_code == 200:
            print("✅ Token is valid")
            return True
        else:
            print(f"❌ Token is invalid: {response.status_code} - {response.text}")
            return False

    def get_new_token(self):
        result = self.app.acquire_token_by_refresh_token(refresh_token=self.refresh_token, scopes=self.scopes)
        print('--------------')
        print(result)

        if "access_token" in result:
            self.token = result["access_token"]
            print("✅ Generated new token successfully!")
            supabase_service.update_access_token(self.email, self.token)
            return self.token
        else:
            raise Exception("❌ Could not get token: " + str(result))
    
    async def get_headers(self):
        token = self.token
        is_valid_token = await self.validate_token(token)
        if not is_valid_token:
            token = self.get_new_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def make_request(self, method, endpoint, data=None, params=None):
        headers = await self.get_headers()
        url = f"https://graph.microsoft.com/v1.0/{endpoint}"

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params
            )

        if response.status_code >= 400:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            raise Exception(f"API error: {response.status_code} - {response.text}")

        if response.content and response.content.strip():
            return response.json()
        return None
