import requests
import httpx
import asyncio
import time
import re
from typing import Optional, Dict, Any, List, Literal, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import os
import logging

logger = logging.getLogger(__name__)

# Constants
MAX_MESSAGE_LENGTH = 4000
TELEGRAM_API_BASE = "https://api.telegram.org/bot"
RATE_LIMIT_DELAY = 0.1  # Delay between requests in seconds

@dataclass
class RetryConfig:
    """Retry configuration for API calls"""
    max_attempts: int = 3
    backoff: float = 2.0  # Exponential backoff multiplier
    initial_delay: float = 0.5

@dataclass
class SendOptions:
    """Options for sending messages"""
    token: Optional[str] = None
    timeout: int = 30
    retry: Optional[RetryConfig] = None
    media_url: Optional[str] = None
    thread_id: Optional[int] = None
    reply_to: Optional[int] = None
    buttons: Optional[List[List[Dict[str, str]]]] = None
    silent: bool = False
    text_mode: Literal["html", "markdown"] = "markdown"
    force_document: bool = False
    parse_mode: Optional[str] = None

class RateLimiter:
    """Simple rate limiter"""
    def __init__(self, delay: float = RATE_LIMIT_DELAY):
        self.delay = delay
        self.last_request_time = 0.0

    def wait(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_request_time = time.time()

class TelegramSender:
    """
    Telegram Bot API wrapper with support for messages, reactions, edits, and more.
    Similar to OpenClaw Telegram extension's send.ts
    """

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not provided and not in environment variables")
        self.base_url = f"{TELEGRAM_API_BASE}{self.token}"
        self.rate_limiter = RateLimiter()
        self.session = requests.Session()
        self.chat_id_cache: Dict[str, str] = {}

    def _resolve_token(self, token: Optional[str]) -> str:
        """Resolve token from parameter or instance"""
        if token:
            return token
        if not self.token:
            raise ValueError("No Telegram bot token provided")
        return self.token

    async def _resolve_chat_id(self, target: str) -> str:
        """
        Resolve chat ID from username or numeric ID.
        caches results for usernames.
        """
        # Check if already numeric
        if target.lstrip("-").isdigit():
            return target

        # Check cache
        if target in self.chat_id_cache:
            return self.chat_id_cache[target]

        # Try to resolve via getChat
        try:
            response = await self._api_request("getChat", {"chat_id": target})
            if response.get("ok"):
                chat_id = str(response["result"]["id"])
                self.chat_id_cache[target] = chat_id
                return chat_id
            else:
                raise ValueError(f"Failed to resolve chat ID for {target}: {response.get('description')}")
        except Exception as e:
            raise ValueError(f"Could not resolve chat ID {target}: {str(e)}")

    async def _api_request(self, method: str, params: Dict[str, Any], retry_config: Optional[RetryConfig] = None) -> Dict[str, Any]:
        """
        Make API request to Telegram with retry logic.
        Returns response dictionary with 'ok' field.
        """
        retry = retry_config or RetryConfig()
        url = f"{self.base_url}/{method}"
        
        last_error = None
        for attempt in range(retry.max_attempts):
            try:
                self.rate_limiter.wait()
                response = self.session.post(url, json=params, timeout=30)
                return response.json()
            except Exception as e:
                last_error = e
                if attempt < retry.max_attempts - 1:
                    delay = retry.initial_delay * (retry.backoff ** attempt)
                    await asyncio.sleep(delay)
                    logger.warning(f"API request retry attempt {attempt + 1}/{retry.max_attempts} after {delay}s")
                continue

        if last_error:
            raise last_error
        raise RuntimeError(f"Failed to call {method} after {retry.max_attempts} attempts")

    def _build_inline_keyboard(self, buttons: Optional[List[List[Dict[str, str]]]]) -> Optional[Dict[str, Any]]:
        """Build inline keyboard markup from buttons"""
        if not buttons:
            return None

        inline_keyboard = []
        for row in buttons:
            keyboard_row = []
            for btn in row:
                if btn.get("text") and btn.get("callback_data"):
                    keyboard_row.append({
                        "text": btn["text"],
                        "callback_data": btn["callback_data"]
                    })
            if keyboard_row:
                inline_keyboard.append(keyboard_row)

        return {"inline_keyboard": inline_keyboard} if inline_keyboard else None

    def _chunk_text(self, text: str, limit: int = MAX_MESSAGE_LENGTH) -> List[str]:
        """Split text into chunks respecting limit"""
        if not text:
            return []
        
        chunks = []
        current_pos = 0
        
        while current_pos < len(text):
            chunk = text[current_pos:current_pos + limit]
            chunks.append(chunk)
            current_pos += limit
        
        return chunks

    async def _download_media(self, media_url: str, max_bytes: int = 100 * 1024 * 1024) -> bytes:
        """Download media from URL"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(media_url, timeout=30)
                if len(response.content) > max_bytes:
                    raise ValueError(f"Media file too large: {len(response.content)} > {max_bytes}")
                return response.content
        except Exception as e:
            raise ValueError(f"Failed to download media from {media_url}: {str(e)}")

    def _render_html_text(self, text: str) -> str:
        """Convert markdown-like text to HTML"""
        # Simple markdown to HTML conversion
        html = text
        # Bold: **text** → <b>text</b>
        html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html)
        # Italic: *text* → <i>text</i>
        html = re.sub(r'(?<!\*)\*(.+?)\*(?!\*)', r'<i>\1</i>', html)
        # Code: `text` → <code>text</code>
        html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
        # Links: [text](url) → <a href="url">text</a>
        html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', html)
        return html

    async def send_message(
        self,
        to: str,
        text: str,
        **opts
    ) -> Dict[str, Any]:
        """
        Send a text message to a chat.
        Returns: {"ok": True, "message_id": "...", "chat_id": "..."}
        """
        try:
            options = SendOptions(**{k: v for k, v in opts.items() if hasattr(SendOptions, k)})
            
            chat_id = await self._resolve_chat_id(to)
            
            # Chunk text if too long
            chunks = self._chunk_text(text)
            if not chunks:
                raise ValueError("Message text is empty")
            
            last_message_id = None
            
            for i, chunk in enumerate(chunks):
                params: Dict[str, Any] = {
                    "chat_id": chat_id,
                    "text": chunk,
                }
                
                if options.silent:
                    params["disable_notification"] = True
                
                # Add parse mode
                if options.text_mode == "html":
                    params["parse_mode"] = "HTML"
                else:
                    params["parse_mode"] = "Markdown"
                
                # Add thread_id if provided
                if options.thread_id:
                    params["message_thread_id"] = options.thread_id
                
                # Add reply_to if provided
                if options.reply_to:
                    params["reply_to_message_id"] = options.reply_to
                
                # Add buttons only to last message
                if i == len(chunks) - 1 and options.buttons:
                    keyboard = self._build_inline_keyboard(options.buttons)
                    if keyboard:
                        params["reply_markup"] = keyboard
                
                response = await self._api_request("sendMessage", params, options.retry)
                
                if not response.get("ok"):
                    return {
                        "ok": False,
                        "error": response.get("description", "Unknown error")
                    }
                
                last_message_id = response["result"]["message_id"]
            
            return {
                "ok": True,
                "message_id": str(last_message_id),
                "chat_id": chat_id
            }
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return {"ok": False, "error": str(e)}

    async def send_typing(
        self,
        to: str,
        **opts
    ) -> Dict[str, Any]:
        """
        Send typing indicator.
        Returns {"ok": True}
        """
        try:
            chat_id = await self._resolve_chat_id(to)
            options = SendOptions(**{k: v for k, v in opts.items() if hasattr(SendOptions, k)})
            
            params: Dict[str, Any] = {
                "chat_id": chat_id,
                "action": "typing"
            }
            
            if options.thread_id:
                params["message_thread_id"] = options.thread_id
            
            response = await self._api_request("sendChatAction", params, options.retry)
            
            if response.get("ok"):
                return {"ok": True}
            else:
                return {
                    "ok": False,
                    "error": response.get("description", "Unknown error")
                }
        except Exception as e:
            logger.error(f"Error sending typing: {str(e)}")
            return {"ok": False, "error": str(e)}

    async def react_message(
        self,
        chat_id: Union[str, int],
        message_id: Union[str, int],
        emoji: str,
        **opts
    ) -> Dict[str, Any]:
        """
        Add reaction to a message.
        Returns {"ok": True} or {"ok": False, "error": "..."}
        """
        try:
            chat_id_str = str(chat_id)
            message_id_int = int(message_id)
            options = SendOptions(**{k: v for k, v in opts.items() if hasattr(SendOptions, k)})
            
            params: Dict[str, Any] = {
                "chat_id": chat_id_str,
                "message_id": message_id_int,
                "reaction": [{
                    "type": "emoji",
                    "emoji": emoji.strip()
                }]
            }
            
            response = await self._api_request("setMessageReaction", params, options.retry)
            
            if response.get("ok"):
                return {"ok": True}
            else:
                return {
                    "ok": False,
                    "error": response.get("description", "Unknown error")
                }
        except Exception as e:
            logger.error(f"Error reacting to message: {str(e)}")
            return {"ok": False, "error": str(e)}

    async def delete_message(
        self,
        chat_id: Union[str, int],
        message_id: Union[str, int],
        **opts
    ) -> Dict[str, Any]:
        """
        Delete a message.
        Returns {"ok": True}
        """
        try:
            chat_id_str = str(chat_id)
            message_id_int = int(message_id)
            options = SendOptions(**{k: v for k, v in opts.items() if hasattr(SendOptions, k)})
            
            params = {
                "chat_id": chat_id_str,
                "message_id": message_id_int
            }
            
            response = await self._api_request("deleteMessage", params, options.retry)
            
            if response.get("ok"):
                return {"ok": True}
            else:
                return {
                    "ok": False,
                    "error": response.get("description", "Unknown error")
                }
        except Exception as e:
            logger.error(f"Error deleting message: {str(e)}")
            return {"ok": False, "error": str(e)}

    async def edit_message(
        self,
        chat_id: Union[str, int],
        message_id: Union[str, int],
        text: str,
        **opts
    ) -> Dict[str, Any]:
        """
        Edit an existing message.
        Returns {"ok": True, "message_id": "...", "chat_id": "..."}
        """
        try:
            chat_id_str = str(chat_id)
            message_id_int = int(message_id)
            options = SendOptions(**{k: v for k, v in opts.items() if hasattr(SendOptions, k)})
            
            params: Dict[str, Any] = {
                "chat_id": chat_id_str,
                "message_id": message_id_int,
                "text": text
            }
            
            # Add parse mode
            if options.text_mode == "html":
                params["parse_mode"] = "HTML"
            else:
                params["parse_mode"] = "Markdown"
            
            # Add buttons if provided
            if options.buttons:
                keyboard = self._build_inline_keyboard(options.buttons)
                if keyboard:
                    params["reply_markup"] = keyboard
            
            response = await self._api_request("editMessageText", params, options.retry)
            
            if response.get("ok"):
                return {
                    "ok": True,
                    "message_id": str(message_id_int),
                    "chat_id": chat_id_str
                }
            else:
                return {
                    "ok": False,
                    "error": response.get("description", "Unknown error")
                }
        except Exception as e:
            logger.error(f"Error editing message: {str(e)}")
            return {"ok": False, "error": str(e)}

    async def send_sticker(
        self,
        to: str,
        file_id: str,
        **opts
    ) -> Dict[str, Any]:
        """
        Send a sticker.
        Returns {"ok": True, "message_id": "...", "chat_id": "..."}
        """
        try:
            chat_id = await self._resolve_chat_id(to)
            options = SendOptions(**{k: v for k, v in opts.items() if hasattr(SendOptions, k)})
            
            params: Dict[str, Any] = {
                "chat_id": chat_id,
                "sticker": file_id
            }
            
            if options.silent:
                params["disable_notification"] = True
            
            if options.thread_id:
                params["message_thread_id"] = options.thread_id
            
            if options.reply_to:
                params["reply_to_message_id"] = options.reply_to
            
            response = await self._api_request("sendSticker", params, options.retry)
            
            if response.get("ok"):
                return {
                    "ok": True,
                    "message_id": str(response["result"]["message_id"]),
                    "chat_id": chat_id
                }
            else:
                return {
                    "ok": False,
                    "error": response.get("description", "Unknown error")
                }
        except Exception as e:
            logger.error(f"Error sending sticker: {str(e)}")
            return {"ok": False, "error": str(e)}

    async def send_poll(
        self,
        to: str,
        poll_data: Dict[str, Any],
        **opts
    ) -> Dict[str, Any]:
        """
        Send a poll.
        poll_data should contain: question, options, poll_type (quiz/regular)
        Returns {"ok": True, "message_id": "...", "chat_id": "..."}
        """
        try:
            chat_id = await self._resolve_chat_id(to)
            options = SendOptions(**{k: v for k, v in opts.items() if hasattr(SendOptions, k)})
            
            params: Dict[str, Any] = {
                "chat_id": chat_id,
                "question": poll_data.get("question", ""),
                "options": poll_data.get("options", []),
                "type": poll_data.get("poll_type", "regular")
            }
            
            # Add optional fields
            if "is_anonymous" in poll_data:
                params["is_anonymous"] = poll_data["is_anonymous"]
            
            if "allows_multiple_answers" in poll_data:
                params["allows_multiple_answers"] = poll_data["allows_multiple_answers"]
            
            if "correct_option_id" in poll_data:
                params["correct_option_id"] = poll_data["correct_option_id"]
            
            if options.silent:
                params["disable_notification"] = True
            
            if options.thread_id:
                params["message_thread_id"] = options.thread_id
            
            if options.reply_to:
                params["reply_to_message_id"] = options.reply_to
            
            response = await self._api_request("sendPoll", params, options.retry)
            
            if response.get("ok"):
                return {
                    "ok": True,
                    "message_id": str(response["result"]["message_id"]),
                    "chat_id": chat_id
                }
            else:
                return {
                    "ok": False,
                    "error": response.get("description", "Unknown error")
                }
        except Exception as e:
            logger.error(f"Error sending poll: {str(e)}")
            return {"ok": False, "error": str(e)}

    async def pin_message(
        self,
        chat_id: Union[str, int],
        message_id: Union[str, int],
        **opts
    ) -> Dict[str, Any]:
        """
        Pin a message in a chat.
        Returns {"ok": True, "message_id": "...", "chat_id": "..."}
        """
        try:
            chat_id_str = str(chat_id)
            message_id_int = int(message_id)
            options = SendOptions(**{k: v for k, v in opts.items() if hasattr(SendOptions, k)})
            
            params: Dict[str, Any] = {
                "chat_id": chat_id_str,
                "message_id": message_id_int,
                "disable_notification": True
            }
            
            response = await self._api_request("pinChatMessage", params, options.retry)
            
            if response.get("ok"):
                return {
                    "ok": True,
                    "message_id": str(message_id_int),
                    "chat_id": chat_id_str
                }
            else:
                return {
                    "ok": False,
                    "error": response.get("description", "Unknown error")
                }
        except Exception as e:
            logger.error(f"Error pinning message: {str(e)}")
            return {"ok": False, "error": str(e)}

    async def create_forum_topic(
        self,
        chat_id: Union[str, int],
        name: str,
        **opts
    ) -> Dict[str, Any]:
        """
        Create a forum topic in a supergroup.
        Returns {"ok": True, "topic": {...}}
        """
        try:
            chat_id_str = str(chat_id)
            options = SendOptions(**{k: v for k, v in opts.items() if hasattr(SendOptions, k)})
            
            if not name or not name.strip():
                raise ValueError("Forum topic name is required")
            
            if len(name) > 128:
                raise ValueError("Forum topic name must be 128 characters or fewer")
            
            params: Dict[str, Any] = {
                "chat_id": chat_id_str,
                "name": name.strip()
            }
            
            # Add icon emoji if provided
            if opts.get("icon_emoji"):
                params["icon_color"] = opts.get("icon_color", 7322096)
                # Note: icon_emoji_id requires specific emoji custom IDs
                # For now, we'll just use default icon
            
            response = await self._api_request("createForumTopic", params, options.retry)
            
            if response.get("ok"):
                return {
                    "ok": True,
                    "topic": response["result"]
                }
            else:
                return {
                    "ok": False,
                    "error": response.get("description", "Unknown error")
                }
        except Exception as e:
            logger.error(f"Error creating forum topic: {str(e)}")
            return {"ok": False, "error": str(e)}

    async def unpin_message(
        self,
        chat_id: Union[str, int],
        message_id: Optional[Union[str, int]] = None,
        **opts
    ) -> Dict[str, Any]:
        """
        Unpin a message in a chat. If message_id is not provided, unpins the currently pinned message.
        Returns {"ok": True, "chat_id": "...", "message_id": "..."}
        """
        try:
            chat_id_str = str(chat_id)
            options = SendOptions(**{k: v for k, v in opts.items() if hasattr(SendOptions, k)})
            
            params: Dict[str, Any] = {
                "chat_id": chat_id_str
            }
            
            # If message_id is provided, unpin specific message
            if message_id is not None:
                message_id_int = int(message_id)
                params["message_id"] = message_id_int
            
            response = await self._api_request("unpinChatMessage", params, options.retry)
            
            if response.get("ok"):
                return {
                    "ok": True,
                    "chat_id": chat_id_str,
                    "message_id": str(message_id) if message_id else None
                }
            else:
                return {
                    "ok": False,
                    "error": response.get("description", "Unknown error")
                }
        except Exception as e:
            logger.error(f"Error unpinning message: {str(e)}")
            return {"ok": False, "error": str(e)}

    async def edit_message_reply_markup(
        self,
        chat_id: Union[str, int],
        message_id: Union[str, int],
        buttons: Optional[List[List[Dict[str, str]]]] = None,
        **opts
    ) -> Dict[str, Any]:
        """
        Edit the reply markup (inline keyboard) of a message.
        Returns {"ok": True, "message_id": "...", "chat_id": "..."}
        """
        try:
            chat_id_str = str(chat_id)
            message_id_int = int(message_id)
            options = SendOptions(**{k: v for k, v in opts.items() if hasattr(SendOptions, k)})
            
            params: Dict[str, Any] = {
                "chat_id": chat_id_str,
                "message_id": message_id_int
            }
            
            # Build inline keyboard
            if buttons:
                keyboard = self._build_inline_keyboard(buttons)
                if keyboard:
                    params["reply_markup"] = keyboard
            else:
                # Remove keyboard by setting empty markup
                params["reply_markup"] = {"inline_keyboard": []}
            
            response = await self._api_request("editMessageReplyMarkup", params, options.retry)
            
            if response.get("ok"):
                return {
                    "ok": True,
                    "message_id": str(message_id_int),
                    "chat_id": chat_id_str
                }
            else:
                return {
                    "ok": False,
                    "error": response.get("description", "Unknown error")
                }
        except Exception as e:
            logger.error(f"Error editing message reply markup: {str(e)}")
            return {"ok": False, "error": str(e)}

    async def edit_forum_topic(
        self,
        chat_id: Union[str, int],
        message_thread_id: int,
        **opts
    ) -> Dict[str, Any]:
        """
        Edit a forum topic (name and/or icon).
        Returns {"ok": True}
        """
        try:
            chat_id_str = str(chat_id)
            options = SendOptions(**{k: v for k, v in opts.items() if hasattr(SendOptions, k)})
            
            params: Dict[str, Any] = {
                "chat_id": chat_id_str,
                "message_thread_id": message_thread_id
            }
            
            # Add name if provided
            if opts.get("name"):
                name = opts["name"].strip()
                if len(name) > 128:
                    raise ValueError("Forum topic name must be 128 characters or fewer")
                params["name"] = name
            
            # Add icon color if provided
            if opts.get("icon_color"):
                params["icon_color"] = opts["icon_color"]
            
            # Add custom emoji ID if provided
            if opts.get("icon_custom_emoji_id"):
                params["icon_custom_emoji_id"] = opts["icon_custom_emoji_id"]
            
            response = await self._api_request("editForumTopic", params, options.retry)
            
            if response.get("ok"):
                return {"ok": True}
            else:
                return {
                    "ok": False,
                    "error": response.get("description", "Unknown error")
                }
        except Exception as e:
            logger.error(f"Error editing forum topic: {str(e)}")
            return {"ok": False, "error": str(e)}

    async def rename_forum_topic(
        self,
        chat_id: Union[str, int],
        message_thread_id: int,
        name: str,
        **opts
    ) -> Dict[str, Any]:
        """
        Rename a forum topic.
        Returns {"ok": True}
        """
        try:
            chat_id_str = str(chat_id)
            options = SendOptions(**{k: v for k, v in opts.items() if hasattr(SendOptions, k)})
            
            if not name or not name.strip():
                raise ValueError("Forum topic name is required")
            
            if len(name) > 128:
                raise ValueError("Forum topic name must be 128 characters or fewer")
            
            params: Dict[str, Any] = {
                "chat_id": chat_id_str,
                "message_thread_id": message_thread_id,
                "name": name.strip()
            }
            
            response = await self._api_request("editForumTopic", params, options.retry)
            
            if response.get("ok"):
                return {"ok": True}
            else:
                return {
                    "ok": False,
                    "error": response.get("description", "Unknown error")
                }
        except Exception as e:
            logger.error(f"Error renaming forum topic: {str(e)}")
            return {"ok": False, "error": str(e)}


# Core Utilities
def resolve_telegram_api_context(token: str) -> Dict[str, Any]:
    """
    Initialize Telegram API client with token and config.
    Returns: {"cfg": {...}, "account": {...}, "api": TelegramSender instance}
    """
    if not token:
        raise ValueError("Telegram bot token is required")
    
    sender = TelegramSender(token)
    return {
        "cfg": {"token": token},
        "account": {"bot_token": token},
        "api": sender
    }


async def resolve_chat_id(to: str, api: TelegramSender) -> str:
    """
    Convert username to numeric chat ID.
    """
    return await api._resolve_chat_id(to)


def create_telegram_retry_runner(retry_config: Optional[RetryConfig] = None) -> RetryConfig:
    """
    Create retry logic with exponential backoff.
    """
    return retry_config or RetryConfig()


def with_telegram_html_parse_fallback(text: str, api_instance: TelegramSender) -> str:
    """
    Try HTML format, fallback to plain text if parse error.
    """
    try:
        return api_instance._render_html_text(text)
    except Exception:
        return text


def with_telegram_thread_fallback(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retry without thread ID if thread not found.
    """
    params_copy = params.copy()
    if "message_thread_id" in params_copy:
        del params_copy["message_thread_id"]
    return params_copy


def build_telegram_thread_reply_params(thread_id: Optional[int] = None, reply_to: Optional[int] = None) -> Dict[str, Any]:
    """
    Build thread/reply parameters for API calls.
    """
    params = {}
    if thread_id:
        params["message_thread_id"] = thread_id
    if reply_to:
        params["reply_to_message_id"] = reply_to
    return params


def build_inline_keyboard(buttons: List[List[Dict[str, str]]]) -> Dict[str, Any]:
    """
    Convert button array to Telegram InlineKeyboardMarkup.
    """
    if not buttons:
        return {"inline_keyboard": []}
    
    inline_keyboard = []
    for row in buttons:
        keyboard_row = []
        for btn in row:
            if btn.get("text") and btn.get("callback_data"):
                keyboard_row.append({
                    "text": btn["text"],
                    "callback_data": btn["callback_data"]
                })
        if keyboard_row:
            inline_keyboard.append(keyboard_row)
    
    return {"inline_keyboard": inline_keyboard}


def split_telegram_html_chunks(text: str, limit: int = MAX_MESSAGE_LENGTH) -> List[str]:
    """
    Chunk HTML text according to Telegram limits.
    """
    if not text:
        return []
    
    chunks = []
    current_pos = 0
    
    while current_pos < len(text):
        chunk = text[current_pos:current_pos + limit]
        chunks.append(chunk)
        current_pos += limit
    
    return chunks


def render_telegram_html_text(text: str) -> str:
    """
    Convert Markdown to HTML for Telegram.
    """
    # Simple markdown to HTML conversion
    html = text
    # Bold: **text** → <b>text</b>
    html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html)
    # Italic: *text* → <i>text</i>
    html = re.sub(r'(?<!\*)\*(.+?)\*(?!\*)', r'<i>\1</i>', html)
    # Code: `text` → <code>text</code>
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
    # Links: [text](url) → <a href="url">text</a>
    html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', html)
    return html


# Error Handling Functions
def is_telegram_html_parse_error(err: Exception) -> bool:
    """Check if error is HTML parse failed"""
    error_msg = str(err).lower()
    return "can't parse entities" in error_msg or "bad html" in error_msg


def is_telegram_thread_not_found_error(err: Exception) -> bool:
    """Check if error is thread not found"""
    error_msg = str(err).lower()
    return "thread not found" in error_msg or "message thread not found" in error_msg


def is_telegram_message_not_modified_error(err: Exception) -> bool:
    """Check if error is message unchanged"""
    error_msg = str(err).lower()
    return "message is not modified" in error_msg


def is_recoverable_telegram_network_error(err: Exception) -> bool:
    """Check if network error is recoverable"""
    error_msg = str(err).lower()
    return any(keyword in error_msg for keyword in [
        "timeout", "connection", "network", "temporary", "retry"
    ])


# Media Type Mappings
MEDIA_TYPE_MAPPINGS = {
    "image": "sendPhoto",
    "video": "sendVideo", 
    "audio": "sendAudio",
    "gif": "sendAnimation",
    "document": "sendDocument"
}


# Main Function Wrappers (matching the requested API)
async def sendMessageTelegram(to: str, text: str, opts: Dict[str, Any]) -> Dict[str, Any]:
    """Send text message to Telegram chat"""
    api = TelegramSender(opts.get("token"))
    return await api.send_message(to, text, **opts)


async def sendTypingTelegram(to: str, opts: Dict[str, Any]) -> Dict[str, Any]:
    """Send typing indicator"""
    api = TelegramSender(opts.get("token"))
    return await api.send_typing(to, **opts)


async def reactMessageTelegram(chat_id: Union[str, int], message_id: Union[str, int], emoji: str, opts: Dict[str, Any]) -> Dict[str, Any]:
    """React to message with emoji"""
    api = TelegramSender(opts.get("token"))
    return await api.react_message(chat_id, message_id, emoji, **opts)


async def deleteMessageTelegram(chat_id: Union[str, int], message_id: Union[str, int], opts: Dict[str, Any]) -> Dict[str, Any]:
    """Delete message"""
    api = TelegramSender(opts.get("token"))
    return await api.delete_message(chat_id, message_id, **opts)


async def pinMessageTelegram(chat_id: Union[str, int], message_id: Union[str, int], opts: Dict[str, Any]) -> Dict[str, Any]:
    """Pin message in chat"""
    api = TelegramSender(opts.get("token"))
    return await api.pin_message(chat_id, message_id, **opts)


async def unpinMessageTelegram(chat_id: Union[str, int], message_id: Optional[Union[str, int]] = None, opts: Dict[str, Any] = None) -> Dict[str, Any]:
    """Unpin message (or active pin)"""
    if opts is None:
        opts = {}
    api = TelegramSender(opts.get("token"))
    return await api.unpin_message(chat_id, message_id, **opts)


async def editMessageTelegram(chat_id: Union[str, int], message_id: Union[str, int], text: str, opts: Dict[str, Any]) -> Dict[str, Any]:
    """Edit message content"""
    api = TelegramSender(opts.get("token"))
    return await api.edit_message(chat_id, message_id, text, **opts)


async def editMessageReplyMarkupTelegram(chat_id: Union[str, int], message_id: Union[str, int], buttons: List[List[Dict[str, str]]], opts: Dict[str, Any]) -> Dict[str, Any]:
    """Edit inline keyboard buttons"""
    api = TelegramSender(opts.get("token"))
    return await api.edit_message_reply_markup(chat_id, message_id, buttons, **opts)


async def sendStickerTelegram(to: str, file_id: str, opts: Dict[str, Any]) -> Dict[str, Any]:
    """Send sticker by file_id"""
    api = TelegramSender(opts.get("token"))
    return await api.send_sticker(to, file_id, **opts)


async def sendPollTelegram(to: str, poll: Dict[str, Any], opts: Dict[str, Any]) -> Dict[str, Any]:
    """Send poll/cuộc bỏ phiếu"""
    api = TelegramSender(opts.get("token"))
    return await api.send_poll(to, poll, **opts)


async def createForumTopicTelegram(chat_id: Union[str, int], name: str, opts: Dict[str, Any]) -> Dict[str, Any]:
    """Create forum topic mới"""
    api = TelegramSender(opts.get("token"))
    return await api.create_forum_topic(chat_id, name, **opts)


async def editForumTopicTelegram(chat_id: Union[str, int], message_thread_id: int, opts: Dict[str, Any]) -> Dict[str, Any]:
    """Edit forum topic (name/icon)"""
    api = TelegramSender(opts.get("token"))
    return await api.edit_forum_topic(chat_id, message_thread_id, **opts)


async def renameForumTopicTelegram(chat_id: Union[str, int], message_thread_id: int, name: str, opts: Dict[str, Any]) -> Dict[str, Any]:
    """Rename forum topic"""
    api = TelegramSender(opts.get("token"))
    return await api.rename_forum_topic(chat_id, message_thread_id, name, **opts)
