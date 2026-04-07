"""
Telegram Utilities and Error Handling
Retry logic, HTML parsing, thread handling, logging (từ send.ts và các files khác)
"""

import logging
import re
import time
import functools
from typing import Callable, Optional, Any, Dict, List, TypeVar, Tuple
from html.parser import HTMLParser
import traceback

logger = logging.getLogger(__name__)

# Type variable for generic functions
T = TypeVar('T')


# ============ Custom Exceptions ============

class TelegramError(Exception):
    """Base exception for Telegram errors"""
    pass


class TelegramAuthError(TelegramError):
    """Authentication/authorization error (401)"""
    pass


class TelegramRateLimitError(TelegramError):
    """Rate limit error (429)"""
    pass


class TelegramHTMLParseError(TelegramError):
    """HTML parsing error"""
    pass


class TelegramThreadNotFoundError(TelegramError):
    """Thread/topic not found"""
    pass


class TelegramMessageNotModifiedError(TelegramError):
    """Message not modified error"""
    pass


class TelegramNetworkError(TelegramError):
    """Network/connection error"""
    pass


# ============ Error Detection Functions ============

def is_auth_error(error: Exception) -> bool:
    """Check if error is authentication error"""
    error_msg = str(error).lower()
    return any(keyword in error_msg for keyword in [
        "401", "unauthorized", "invalid token", "bot token"
    ])


def is_rate_limit_error(error: Exception) -> bool:
    """Check if error is rate limit"""
    error_msg = str(error).lower()
    return any(keyword in error_msg for keyword in [
        "429", "too many requests", "rate limit", "retry-after"
    ])


def is_html_parse_error(error: Exception) -> bool:
    """Check if error is HTML parse error"""
    error_msg = str(error).lower()
    return any(keyword in error_msg for keyword in [
        "can't parse entities", "parse error", "html malformed",
        "bad tag", "invalid tag", "bad html"
    ])


def is_thread_not_found_error(error: Exception) -> bool:
    """Check if error is thread not found"""
    error_msg = str(error).lower()
    return any(keyword in error_msg for keyword in [
        "thread not found", "message thread not found", 
        "topic not found", "bad request"
    ])


def is_message_not_modified_error(error: Exception) -> bool:
    """Check if error is message not modified"""
    error_msg = str(error).lower()
    return "message is not modified" in error_msg


def is_recoverable_error(error: Exception) -> bool:
    """Check if error is recoverable (can retry)"""
    error_msg = str(error).lower()
    return any(keyword in error_msg for keyword in [
        "timeout", "connection", "network", "temporary", "500", "503",
        "connection reset", "broken pipe"
    ])


# ============ Retry Decorator ============

def retry_on_failure(
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 10.0,
    backoff_multiplier: float = 2.0,
    retry_on: Optional[Callable[[Exception], bool]] = None
):
    """
    Decorator for retrying with exponential backoff
    
    Usage:
        @retry_on_failure(max_attempts=3)
        def my_function():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = base_delay
            last_error = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e

                    # Check if we should retry this error
                    if retry_on and not retry_on(e):
                        raise

                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                        delay = min(delay * backoff_multiplier, max_delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {str(e)}"
                        )

            if last_error:
                raise last_error

        return wrapper
    return decorator


# ============ HTML Utilities ============

class PlainTextExtractor(HTMLParser):
    """Extract plain text from HTML"""

    def __init__(self):
        super().__init__()
        self.text_parts: List[str] = []
        self._in_tag = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        """Handle start tags"""
        if tag in ['br', 'p', 'div']:
            self.text_parts.append('\n')

    def handle_endtag(self, tag: str):
        """Handle end tags"""
        if tag in ['p', 'div', 'li']:
            self.text_parts.append('\n')

    def handle_data(self, data: str):
        """Handle text data"""
        if data:
            self.text_parts.append(data.strip())

    def get_text(self) -> str:
        """Get extracted text"""
        text = ''.join(self.text_parts)
        # Clean up multiple newlines
        text = re.sub(r'\n\s*\n+', '\n', text)
        return text.strip()


def strip_html_tags(html_text: str) -> str:
    """Remove all HTML tags from text"""
    return re.sub(r'<[^>]+>', '', html_text)


def html_to_plain_text(html_text: str) -> str:
    """Convert HTML to plain text"""
    try:
        parser = PlainTextExtractor()
        parser.feed(html_text)
        return parser.get_text()
    except Exception as e:
        logger.warning(f"Error parsing HTML: {str(e)}")
        # Fallback to simple tag stripping
        return strip_html_tags(html_text)


def with_html_parse_fallback(func: Callable) -> Callable:
    """
    Decorator for HTML parsing with fallback to plain text
    If HTML parsing fails, falls back to plain text
    """
    @functools.wraps(func)
    def wrapper(text: str, *args, **kwargs):
        try:
            # Try with HTML mode
            kwargs['text_mode'] = 'html'
            return func(text, *args, **kwargs)
        except Exception as e:
            if is_html_parse_error(e):
                logger.debug(f"HTML parse failed, trying plain text fallback: {str(e)}")
                try:
                    # Fallback to plain text
                    kwargs['text_mode'] = 'plain'
                    return func(text, *args, **kwargs)
                except Exception as fallback_e:
                    logger.error(f"Plain text fallback also failed: {str(fallback_e)}")
                    raise

            raise

    return wrapper


# ============ Thread Handling ============

def strip_thread_id(target: str) -> str:
    """
    Remove thread/topic ID from target
    Used for fallback when thread not supported
    
    Examples:
        "123456789/thread:456" -> "123456789"
        "channel@topic123" -> "channel"
    """
    # Remove /thread:id
    target = re.sub(r'/thread:\d+', '', target)

    # Remove @topic patterns
    target = re.sub(r'@[a-zA-Z0-9_]+', '', target)

    return target.strip()


def with_thread_fallback(func: Callable) -> Callable:
    """
    Decorator for thread/topic handling with fallback
    If thread not supported, retry without thread ID
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if is_thread_not_found_error(e):
                logger.debug(f"Thread not found, retrying without thread: {str(e)}")

                # Remove thread_id from kwargs if present
                if 'thread_id' in kwargs:
                    kwargs.pop('thread_id')

                # Retry without thread
                try:
                    return func(*args, **kwargs)
                except Exception as retry_e:
                    logger.error(f"Retry without thread also failed: {str(retry_e)}")
                    raise

            raise

    return wrapper


# ============ Markdown/HTML Utilities ============

def markdown_to_html(markdown_text: str) -> str:
    """
    Convert Markdown-like syntax to HTML
    Supports: **bold**, *italic*, `code`, [link](url)
    """
    html = markdown_text

    # Escape special characters first
    html = html.replace('&', '&amp;')
    html = html.replace('<', '&lt;')
    html = html.replace('>', '&gt;')

    # Bold: **text** → <b>text</b>
    html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html)

    # Italic: *text* → <i>text</i>
    html = re.sub(r'(?<!\*)\*(.+?)\*(?!\*)', r'<i>\1</i>', html)

    # Code: `text` → <code>text</code>
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)

    # Links: [text](url) → <a href="url">text</a>
    html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', html)

    return html


def sanitize_html(html_text: str) -> str:
    """
    Sanitize HTML for Telegram
    Removes dangerous tags/attributes
    """
    # Only allow safe tags
    allowed_tags = ['b', 'i', 'u', 's', 'code', 'pre', 'a', 'br', 'strong', 'em']

    for tag in re.findall(r'<([a-z]+)', html_text):
        if tag not in allowed_tags:
            html_text = re.sub(f'<{tag}[^>]*>', '', html_text)
            html_text = re.sub(f'</{tag}>', '', html_text)

    # Remove event handlers
    html_text = re.sub(r'\s+on\w+\s*=', ' ', html_text)

    return html_text


# ============ Text Utilities ============

def split_message(text: str, max_length: int = 4096) -> List[str]:
    """
    Split long message into chunks
    Tries to split on newlines or spaces to preserve formatting
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""

    # Try to split on paragraphs first
    paragraphs = text.split('\n\n')

    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 2 <= max_length:
            current_chunk += paragraph + '\n\n'
        else:
            if current_chunk:
                chunks.append(current_chunk.rstrip())
            current_chunk = paragraph + '\n\n'

    if current_chunk:
        chunks.append(current_chunk.rstrip())

    # If any chunk is still too long, split by lines
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > max_length:
            lines = chunk.split('\n')
            current = ""
            for line in lines:
                if len(current) + len(line) + 1 <= max_length:
                    current += line + '\n'
                else:
                    if current:
                        final_chunks.append(current.rstrip())
                    current = line + '\n'
            if current:
                final_chunks.append(current.rstrip())
        else:
            final_chunks.append(chunk)

    return final_chunks


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text with suffix"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


# ============ Logging Utilities ============

def log_api_call(
    method: str,
    params: Dict[str, Any],
    response: Optional[Dict[str, Any]] = None,
    error: Optional[Exception] = None
):
    """Log API call for debugging"""
    # Don't log sensitive info
    safe_params = {k: v for k, v in params.items() if k not in ['token']}

    if error:
        logger.error(
            f"API call failed: {method} with params {safe_params}. Error: {str(error)}"
        )
    elif response and response.get('ok'):
        logger.debug(f"API call succeeded: {method}")
    else:
        logger.warning(f"API call returned error: {method} - {response}")


def log_exception(error: Exception, context: str = "") -> None:
    """Log exception with full traceback"""
    logger.error(
        f"Exception occurred{' in ' + context if context else ''}: {str(error)}\n"
        f"{traceback.format_exc()}"
    )


# ============ Validation Utilities ============

def validate_chat_id(chat_id: str) -> bool:
    """Validate chat ID format"""
    return bool(re.match(r'^-?\d+$', str(chat_id)))


def validate_message_id(message_id: str) -> bool:
    """Validate message ID"""
    return bool(re.match(r'^\d+$', str(message_id)))


def validate_username(username: str) -> bool:
    """Validate Telegram username format"""
    return bool(re.match(r'^@?[a-zA-Z0-9_]{5,32}$', username))


def is_private_chat(chat_id: str) -> bool:
    """Check if chat ID is private (positive number)"""
    try:
        return int(chat_id) > 0
    except ValueError:
        return False


def is_group_chat(chat_id: str) -> bool:
    """Check if chat ID is group/supergroup (negative number)"""
    try:
        id_int = int(chat_id)
        return id_int < 0
    except ValueError:
        return False


def is_channel_chat(chat_id: str) -> bool:
    """Check if chat ID is channel (negative, starts with -100)"""
    return str(chat_id).startswith('-100')
