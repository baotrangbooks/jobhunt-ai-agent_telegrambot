from pydantic import BaseModel
from typing import Literal, Optional

class IncomingMessage(BaseModel):
    user_id: str
    text_content: str
    platform: Literal["zalo", "tele"]
    message_type: Optional[str] = "text"  # text, callback_query, sticker, photo, etc.