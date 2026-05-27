import httpx
import json
import os
from datetime import datetime, timedelta
from typing import Optional

TOKEN_FILE = "tokens.json"

class ZaloManager:
    def __init__(self, app_id: str = "", app_secret: str = "", bot_token: str = ""):
        self.app_id = app_id
        self.app_secret = app_secret
        self.bot_token = bot_token
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.expires_at: Optional[datetime] = None
        if not self.bot_token:
            self.load_tokens()

    def load_tokens(self):
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as f:
                data = json.load(f)
                self.access_token = data.get('access_token')
                self.refresh_token = data.get('refresh_token')
                expires_in = data.get('expires_in')
                if expires_in:
                    self.expires_at = datetime.fromisoformat(expires_in)

    def save_tokens(self):
        data = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_in': self.expires_at.isoformat() if self.expires_at else None
        }
        with open(TOKEN_FILE, 'w') as f:
            json.dump(data, f)

    async def refresh_token_if_needed(self):
        if not self.access_token or (self.expires_at and datetime.now() >= self.expires_at - timedelta(minutes=5)):
            await self.refresh_access_token()

    async def refresh_access_token(self):
        if not self.refresh_token:
            raise ValueError("No refresh token available")

        url = "https://oauth.zaloapp.com/v4/oa/access_token"
        payload = {
            "refresh_token": self.refresh_token,
            "app_id": self.app_id,
            "grant_type": "refresh_token"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            self.access_token = data['access_token']
            self.refresh_token = data['refresh_token']
            self.expires_at = datetime.now() + timedelta(seconds=data['expires_in'])
            self.save_tokens()

    async def send_zalo_message(self, user_id: str, text: str):
        if self.bot_token:
            return await self.send_zalo_bot_message(user_id, text)

        await self.refresh_token_if_needed()

        url = f"https://openapi.zalo.me/v2.0/oa/message?access_token={self.access_token}"
        payload = {
            "recipient": {
                "user_id": user_id
            },
            "message": {
                "text": text
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    async def send_zalo_bot_message(self, chat_id: str, text: str):
        url = f"https://bot-api.zaloplatforms.com/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
            response.raise_for_status()
            return response.json()
