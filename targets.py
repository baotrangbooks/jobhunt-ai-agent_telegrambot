"""
Target Parser and Normalizer
Phân tích và chuẩn hóa chat IDs, usernames, và thread IDs (Tương tự targets.ts)
"""

import re
import logging
from typing import Optional, Dict, Any, Tuple, Literal
from dataclasses import dataclass
import requests

logger = logging.getLogger(__name__)

# Chat type constants
ChatType = Literal["private", "group", "supergroup", "channel"]

@dataclass
class ParsedTarget:
    """Parsed target information"""
    chat_id: str
    username: Optional[str] = None
    thread_id: Optional[int] = None
    chat_type: ChatType = "private"
    is_valid: bool = True
    error: Optional[str] = None

    def __str__(self) -> str:
        """String representation"""
        parts = [f"chat_id={self.chat_id}"]
        if self.username:
            parts.append(f"username={self.username}")
        if self.thread_id:
            parts.append(f"thread_id={self.thread_id}")
        parts.append(f"type={self.chat_type}")
        return f"ParsedTarget({', '.join(parts)})"


class TargetParser:
    """Parse and normalize Telegram targets"""

    # Regex patterns
    USERNAME_PATTERN = re.compile(r'^@?([a-zA-Z0-9_]{5,32})$')
    CHAT_ID_PATTERN = re.compile(r'^-?\d+$')
    THREAD_PATTERN = re.compile(r'^(\d+)/(\d+)$')  # thread_id/message_id format
    MESSAGE_THREAD_PATTERN = re.compile(r'(?:thread|topic):(\d+)')

    # Known prefixes
    GROUP_PREFIX = "group:"
    SUPERGROUP_PREFIX = "supergroup:"
    CHANNEL_PREFIX = "channel:"
    PRIVATE_PREFIX = "private:"

    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = bot_token
        self.id_cache: Dict[str, str] = {}  # Username -> Chat ID cache

    def parse_target(self, target: str, thread_id: Optional[int] = None) -> ParsedTarget:
        """
        Parse target string into structured data
        Supports:
        - Numeric IDs: "123456789", "-123456789"
        - Usernames: "@username", "username"
        - Prefixed: "group:123", "channel:@name"
        - Thread format: "123456789/thread:456"
        """
        if not target or not isinstance(target, str):
            return ParsedTarget(
                chat_id="",
                is_valid=False,
                error="Invalid target: must be non-empty string"
            )

        target = target.strip()

        # Parse prefixed targets
        chat_type: ChatType = "private"
        clean_target = target

        if target.startswith(self.GROUP_PREFIX):
            chat_type = "group"
            clean_target = target[len(self.GROUP_PREFIX):]
        elif target.startswith(self.SUPERGROUP_PREFIX):
            chat_type = "supergroup"
            clean_target = target[len(self.SUPERGROUP_PREFIX):]
        elif target.startswith(self.CHANNEL_PREFIX):
            chat_type = "channel"
            clean_target = target[len(self.CHANNEL_PREFIX):]
        elif target.startswith(self.PRIVATE_PREFIX):
            chat_type = "private"
            clean_target = target[len(self.PRIVATE_PREFIX):]

        # Extract thread ID if present
        thread_match = self.MESSAGE_THREAD_PATTERN.search(clean_target)
        if thread_match:
            thread_id = int(thread_match.group(1))
            clean_target = self.MESSAGE_THREAD_PATTERN.sub("", clean_target).strip()

        # Parse thread format: "chat_id/thread:123"
        if "/thread:" in clean_target:
            parts = clean_target.split("/thread:")
            if len(parts) == 2:
                chat_id_part = parts[0]
                thread_id = int(parts[1])
                clean_target = chat_id_part

        # Parse the main target
        if self.CHAT_ID_PATTERN.match(clean_target):
            # Numeric chat ID
            return ParsedTarget(
                chat_id=clean_target,
                thread_id=thread_id,
                chat_type=chat_type,
                is_valid=True
            )

        elif self.USERNAME_PATTERN.match(clean_target):
            # Username
            username = clean_target.lstrip("@")
            # Try to resolve to chat ID
            chat_id = self._resolve_username_to_id(username)
            return ParsedTarget(
                chat_id=chat_id or username,
                username=username,
                thread_id=thread_id,
                chat_type=chat_type,
                is_valid=bool(chat_id)
            )

        else:
            return ParsedTarget(
                chat_id="",
                thread_id=thread_id,
                chat_type=chat_type,
                is_valid=False,
                error=f"Invalid target format: {target}"
            )

    def normalize_chat_id(self, chat_id: Any) -> str:
        """
        Normalize chat ID to string format
        Handles: int, str, None
        """
        if chat_id is None:
            return ""

        chat_id_str = str(chat_id).strip()

        # Validate format
        if not self.CHAT_ID_PATTERN.match(chat_id_str):
            logger.warning(f"Invalid chat ID format: {chat_id_str}")
            return chat_id_str

        return chat_id_str

    def extract_thread_id(self, target: str) -> Optional[int]:
        """Extract thread ID from target if present"""
        # Format: "thread:123" or "/thread:123"
        match = self.MESSAGE_THREAD_PATTERN.search(target)
        if match:
            return int(match.group(1))

        # Format: "chat_id/thread:123"
        if "/thread:" in target:
            try:
                thread_part = target.split("/thread:")[1]
                return int(thread_part.split()[0])  # Handle any trailing text
            except (IndexError, ValueError):
                pass

        return None

    def build_target_string(
        self,
        chat_id: str,
        thread_id: Optional[int] = None,
        chat_type: ChatType = "private"
    ) -> str:
        """Build target string from components"""
        prefix = ""
        if chat_type == "group":
            prefix = self.GROUP_PREFIX
        elif chat_type == "supergroup":
            prefix = self.SUPERGROUP_PREFIX
        elif chat_type == "channel":
            prefix = self.CHANNEL_PREFIX

        target = f"{prefix}{chat_id}"

        if thread_id:
            target += f"/thread:{thread_id}"

        return target

    def _resolve_username_to_id(self, username: str) -> Optional[str]:
        """
        Resolve username to chat ID using Telegram API
        Caches result for future use
        """
        # Check cache first
        if username in self.id_cache:
            return self.id_cache[username]

        if not self.bot_token:
            logger.warning(f"No bot token available, cannot resolve username: {username}")
            return None

        try:
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/getChat",
                json={"chat_id": f"@{username}"},
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    chat_id = str(data['result']['id'])
                    self.id_cache[username] = chat_id
                    logger.info(f"Resolved @{username} to {chat_id}")
                    return chat_id
                else:
                    logger.warning(f"Failed to resolve @{username}: {data.get('description')}")

            return None

        except Exception as e:
            logger.error(f"Error resolving username {username}: {str(e)}")
            return None

    def validate_target(self, target: str) -> bool:
        """Validate if target is in correct format"""
        parsed = self.parse_target(target)
        return parsed.is_valid and bool(parsed.chat_id)

    def is_username(self, target: str) -> bool:
        """Check if target is a username"""
        return bool(self.USERNAME_PATTERN.match(target.lstrip("@")))

    def is_chat_id(self, target: str) -> bool:
        """Check if target is a chat ID"""
        return bool(self.CHAT_ID_PATTERN.match(target))

    def is_valid_chat_id(self, chat_id: str) -> bool:
        """Validate chat ID format"""
        return bool(self.CHAT_ID_PATTERN.match(str(chat_id)))

    def get_chat_type_from_id(self, chat_id: str) -> ChatType:
        """
        Infer chat type from chat ID format
        Negative IDs that start with -100 are supergroups/channels
        Regular negative IDs are groups
        Positive IDs are private chats
        """
        try:
            id_int = int(chat_id)
            if id_int > 0:
                return "private"
            elif str(chat_id).startswith("-100"):
                return "supergroup"
            else:
                return "group"
        except ValueError:
            return "private"

    def strip_thread_fallback(self, target: ParsedTarget) -> ParsedTarget:
        """
        Create fallback target without thread ID
        Useful for APIs that don't support threads
        """
        fallback = ParsedTarget(
            chat_id=target.chat_id,
            username=target.username,
            thread_id=None,
            chat_type=target.chat_type,
            is_valid=target.is_valid
        )
        return fallback

    def format_target_for_api(self, target: ParsedTarget) -> Dict[str, Any]:
        """Format target for Telegram API call"""
        api_params = {
            "chat_id": target.chat_id,
        }

        if target.thread_id:
            api_params["message_thread_id"] = target.thread_id

        return api_params


# Module-level instance
_parser: Optional[TargetParser] = None


def get_parser(bot_token: Optional[str] = None) -> TargetParser:
    """Get or create global parser"""
    global _parser
    if _parser is None:
        _parser = TargetParser(bot_token)
    return _parser


def parse_target(target: str, thread_id: Optional[int] = None) -> ParsedTarget:
    """Parse target string"""
    return get_parser().parse_target(target, thread_id)


def normalize_chat_id(chat_id: Any) -> str:
    """Normalize chat ID"""
    return get_parser().normalize_chat_id(chat_id)
