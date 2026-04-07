"""
Telegram Channel - Main Channel Logic
Tích hợp core, quản lý routing messages, adapters (Tương tự channel.ts)
"""

import logging
import asyncio
from typing import Optional, Dict, Any, Callable, List, Coroutine
from dataclasses import dataclass
from datetime import datetime

from telegram_sender import TelegramSender
from accounts import get_account_manager, TelegramAccount
from targets import get_parser, ParsedTarget
from runtime import get_runtime_context, RetryConfig as RuntimeRetryConfig
from utils import retry_on_failure, with_html_parse_fallback, log_api_call

logger = logging.getLogger(__name__)


@dataclass
class OutgoingMessage:
    """Outgoing message structure"""
    target: str
    text: str
    thread_id: Optional[int] = None
    media_url: Optional[str] = None
    buttons: Optional[List[List[Dict[str, str]]]] = None
    text_mode: str = "markdown"  # markdown or html
    silent: bool = False
    reply_to: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "target": self.target,
            "text": self.text,
            "thread_id": self.thread_id,
            "media_url": self.media_url,
            "buttons": self.buttons,
            "text_mode": self.text_mode,
            "silent": self.silent,
            "reply_to": self.reply_to
        }


@dataclass
class IncomingMessage:
    """Incoming message structure"""
    message_id: int
    chat_id: str
    user_id: int
    text: str
    timestamp: datetime
    message_type: str = "text"
    thread_id: Optional[int] = None
    reply_to_message_id: Optional[int] = None
    username: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "message_id": self.message_id,
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "text": self.text,
            "timestamp": self.timestamp.isoformat(),
            "message_type": self.message_type,
            "thread_id": self.thread_id,
            "reply_to_message_id": self.reply_to_message_id,
            "username": self.username
        }


class TelegramChannelAdapter:
    """
    Adapter pattern for Telegram channel
    Provides unified interface for send/receive operations
    """

    def __init__(self, account_id: Optional[str] = None):
        self.account_id = account_id
        self.account_manager = get_account_manager()
        self.parser = get_parser()
        self.runtime = get_runtime_context()

    async def send_message(self, message: OutgoingMessage) -> Dict[str, Any]:
        """
        Send message through channel
        """
        try:
            # Get account
            account = self._resolve_account()
            if not account:
                return {"ok": False, "error": "No account available"}

            # Create sender
            sender = TelegramSender(account.token)

            # Parse target
            parsed = self.parser.parse_target(message.target, message.thread_id)
            if not parsed.is_valid:
                return {"ok": False, "error": f"Invalid target: {parsed.error}"}

            # Rate limit
            self.runtime.wait_for_rate_limit(bucket=account.id)

            # Send message
            result = await sender.send_message(
                to=parsed.chat_id,
                text=message.text,
                thread_id=parsed.thread_id,
                media_url=message.media_url,
                buttons=message.buttons,
                text_mode=message.text_mode,
                silent=message.silent,
                reply_to=message.reply_to
            )

            log_api_call("sendMessage", {"chat_id": parsed.chat_id}, result)
            sender.close()
            return result

        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return {"ok": False, "error": str(e)}

    async def edit_message(
        self,
        chat_id: str,
        message_id: int,
        text: str,
        buttons: Optional[List[List[Dict[str, str]]]] = None,
        text_mode: str = "markdown"
    ) -> Dict[str, Any]:
        """Edit existing message"""
        try:
            account = self._resolve_account()
            if not account:
                return {"ok": False, "error": "No account available"}

            sender = TelegramSender(account.token)

            # Rate limit
            self.runtime.wait_for_rate_limit(bucket=account.id)

            result = await sender.edit_message(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                buttons=buttons,
                text_mode=text_mode
            )

            sender.close()
            return result

        except Exception as e:
            logger.error(f"Error editing message: {str(e)}")
            return {"ok": False, "error": str(e)}

    async def delete_message(self, chat_id: str, message_id: int) -> Dict[str, Any]:
        """Delete message"""
        try:
            account = self._resolve_account()
            if not account:
                return {"ok": False, "error": "No account available"}

            sender = TelegramSender(account.token)

            # Rate limit
            self.runtime.wait_for_rate_limit(bucket=account.id)

            result = await sender.delete_message(
                chat_id=chat_id,
                message_id=message_id
            )

            sender.close()
            return result

        except Exception as e:
            logger.error(f"Error deleting message: {str(e)}")
            return {"ok": False, "error": str(e)}

    async def react_message(
        self,
        chat_id: str,
        message_id: int,
        emoji: str
    ) -> Dict[str, Any]:
        """React to message"""
        try:
            account = self._resolve_account()
            if not account:
                return {"ok": False, "error": "No account available"}

            sender = TelegramSender(account.token)

            # Rate limit
            self.runtime.wait_for_rate_limit(bucket=account.id)

            result = await sender.react_message(
                chat_id=chat_id,
                message_id=message_id,
                emoji=emoji
            )

            sender.close()
            return result

        except Exception as e:
            logger.error(f"Error reacting to message: {str(e)}")
            return {"ok": False, "error": str(e)}

    def _resolve_account(self) -> Optional[TelegramAccount]:
        """Resolve account"""
        if self.account_id:
            return self.account_manager.get_account(self.account_id)

        # Fallback to first active account
        return self.account_manager.resolve_account()


class TelegramChannel:
    """
    Main Telegram Channel
    Central component for all Telegram operations
    """

    def __init__(self, account_id: Optional[str] = None):
        self.adapter = TelegramChannelAdapter(account_id)
        self.message_handlers: Dict[str, List[Callable]] = {
            "text": [],
            "media": [],
            "callback": [],
            "error": []
        }
        self.is_running = False

    async def send_via_channel(self, message: OutgoingMessage) -> Dict[str, Any]:
        """Send message via channel"""
        logger.info(f"Sending message to {message.target}")
        return await self.adapter.send_message(message)

    async def receive_message(self, message: IncomingMessage) -> None:
        """Receive and dispatch message"""
        logger.info(f"Received message from {message.user_id}: {message.text[:50]}")

        # Get appropriate handlers
        handlers = self.message_handlers.get(message.message_type, [])

        # Execute handlers
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error(f"Error in message handler: {str(e)}")
                await self._call_error_handlers(e, message)

    def register_handler(
        self,
        message_type: str,
        handler: Callable
    ) -> None:
        """
        Register message handler
        message_type: text, media, callback, error
        """
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []

        self.message_handlers[message_type].append(handler)
        logger.info(f"Registered handler for {message_type} messages")

    def unregister_handler(self, message_type: str, handler: Callable) -> None:
        """Unregister message handler"""
        if message_type in self.message_handlers:
            self.message_handlers[message_type].remove(handler)
            logger.info(f"Unregistered handler for {message_type} messages")

    async def _call_error_handlers(
        self,
        error: Exception,
        message: IncomingMessage
    ) -> None:
        """Call error handlers"""
        error_handlers = self.message_handlers.get("error", [])

        for handler in error_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(error, message)
                else:
                    handler(error, message)
            except Exception as e:
                logger.error(f"Error in error handler: {str(e)}")

    async def start(self) -> None:
        """Start channel"""
        self.is_running = True
        logger.info("Telegram channel started")

    async def stop(self) -> None:
        """Stop channel"""
        self.is_running = False
        logger.info("Telegram channel stopped")

    def is_connected(self) -> bool:
        """Check if channel is connected"""
        account = self.adapter._resolve_account()
        return account is not None and account.is_active


# Global channel instance
_channel: Optional[TelegramChannel] = None


def get_channel(account_id: Optional[str] = None) -> TelegramChannel:
    """Get or create global channel"""
    global _channel
    if _channel is None:
        _channel = TelegramChannel(account_id)
    return _channel


async def send_message(
    target: str,
    text: str,
    thread_id: Optional[int] = None,
    media_url: Optional[str] = None,
    buttons: Optional[List[List[Dict[str, str]]]] = None,
    text_mode: str = "markdown",
    silent: bool = False
) -> Dict[str, Any]:
    """
    Send message through channel
    Convenience function
    """
    channel = get_channel()
    message = OutgoingMessage(
        target=target,
        text=text,
        thread_id=thread_id,
        media_url=media_url,
        buttons=buttons,
        text_mode=text_mode,
        silent=silent
    )
    return await channel.send_via_channel(message)


async def edit_message(
    chat_id: str,
    message_id: int,
    text: str,
    buttons: Optional[List[List[Dict[str, str]]]] = None,
    text_mode: str = "markdown"
) -> Dict[str, Any]:
    """Edit message through channel"""
    channel = get_channel()
    return await channel.adapter.edit_message(chat_id, message_id, text, buttons, text_mode)


async def delete_message(chat_id: str, message_id: int) -> Dict[str, Any]:
    """Delete message through channel"""
    channel = get_channel()
    return await channel.adapter.delete_message(chat_id, message_id)


async def react_message(
    chat_id: str,
    message_id: int,
    emoji: str
) -> Dict[str, Any]:
    """React to message through channel"""
    channel = get_channel()
    return await channel.adapter.react_message(chat_id, message_id, emoji)


def on_text_message(handler: Callable) -> Callable:
    """Decorator to register text message handler"""
    channel = get_channel()
    channel.register_handler("text", handler)
    return handler


def on_media_message(handler: Callable) -> Callable:
    """Decorator to register media message handler"""
    channel = get_channel()
    channel.register_handler("media", handler)
    return handler


def on_callback_query(handler: Callable) -> Callable:
    """Decorator to register callback query handler"""
    channel = get_channel()
    channel.register_handler("callback", handler)
    return handler


def on_error(handler: Callable) -> Callable:
    """Decorator to register error handler"""
    channel = get_channel()
    channel.register_handler("error", handler)
    return handler
