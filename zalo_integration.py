import httpx
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Optional

TOKEN_FILE = "tokens.json"
ZALO_BOT_TEXT_LIMIT = 2000
logger = logging.getLogger(__name__)

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
        chunks = _chunk_zalo_text(text)
        results = []
        for index, chunk in enumerate(chunks, start=1):
            result = await self._send_zalo_bot_message_chunk(chat_id, chunk)
            results.append(result)
            logger.info(
                "Zalo Bot API chunk sent: "
                f"chat_id={chat_id}, chunk={index}/{len(chunks)}, ok={result.get('ok')}"
            )
        if len(results) == 1:
            return results[0]
        return {
            "ok": all(bool(item.get("ok")) for item in results),
            "chunks": len(results),
            "results": results,
        }

    async def _send_zalo_bot_message_chunk(self, chat_id: str, text: str):
        url = f"https://bot-api.zaloplatforms.com/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
            response.raise_for_status()
            data = response.json()
            logger.info(
                "Zalo Bot API sendMessage response: "
                f"chat_id={chat_id}, status={response.status_code}, body={data}"
            )
            return data


def _chunk_zalo_text(text: str, *, limit: int = ZALO_BOT_TEXT_LIMIT) -> list[str]:
    content = str(text or "").strip()
    if not content:
        return [""]
    if len(content) <= limit:
        return [content]

    chunks: list[str] = []
    current = ""
    for block in _split_zalo_blocks(content):
        candidate = f"{current}\n\n{block}".strip() if current else block
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
            current = ""
        if len(block) <= limit:
            current = block
            continue
        chunks.extend(_hard_split_text(block, limit=limit))

    if current:
        chunks.append(current)
    return chunks


def _split_zalo_blocks(text: str) -> list[str]:
    blocks = [block.strip() for block in text.split("\n\n") if block.strip()]
    if len(blocks) > 1:
        return blocks
    return [line.strip() for line in text.splitlines() if line.strip()]


def _hard_split_text(text: str, *, limit: int) -> list[str]:
    chunks: list[str] = []
    remaining = text.strip()
    while len(remaining) > limit:
        split_at = remaining.rfind(" ", 0, limit)
        if split_at < int(limit * 0.6):
            split_at = limit
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks
