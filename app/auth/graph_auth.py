# # type: ignore

import msal
import time
from config import MS_CLIENT_ID, MS_TENANT_ID

class GraphAuth:
    def __init__(self):
        self.client_id = MS_CLIENT_ID
        self.tenant_id = MS_TENANT_ID or "consumers"
        # self.authority = f"https://login.microsoftonline.com/consumers"
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = [
            "Mail.ReadWrite",
            "Mail.Send",
            "MailboxSettings.ReadWrite",
            "Calendars.ReadWrite",
            "Files.ReadWrite",
            "User.Read"
        ]
        self.token = None
        self.token_expires_at = 0
        self.app = msal.PublicClientApplication(self.client_id, authority=self.authority)

    def get_token(self):
        current_time = time.time()
        if self.token and self.token_expires_at > current_time + 300:
            return self.token
        
        # Step 1: Initiate Device Flow
        flow = self.app.initiate_device_flow(scopes=self.scopes)
        if "user_code" not in flow:
            raise Exception("❌ Failed to create device flow. Check your client ID or scopes.")

        print(f"\n👉 To sign in, visit {flow['verification_uri']} and enter the code: {flow['user_code']}\n")

        # Step 2: Wait for user to sign in
        result = self.app.acquire_token_by_device_flow(flow)

        if "access_token" in result:
            self.token = result["access_token"]
            self.token_expires_at = current_time + result.get("expires_in", 3600)
            print("✅ Logged in successfully with delegated permissions!")
            return self.token
        else:
            raise Exception("❌ Could not get token: " + str(result))

    def get_headers(self):
        token = self.get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def make_request(self, method, endpoint, data=None, params=None):
        import requests

        headers = self.get_headers()
        url = f"https://graph.microsoft.com/v1.0/{endpoint}"

        response = requests.request(
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