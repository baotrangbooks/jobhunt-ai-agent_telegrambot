# PATCH DATETIME FIRST - before any other imports
# This fixes compatibility with Python < 3.11 for ai-agent-assistant
import patch_datetime  # type: ignore

from fastapi import FastAPI, HTTPException, Request
from models import IncomingMessage
from telegram_sender import TelegramSender, RetryConfig
from zalo_integration import ZaloManager
from ai_integration import get_ai_integration
from uuid import uuid4
import os
import asyncio
import logging
import json
import re
import hashlib
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
bot_notify_secret = os.getenv("BOT_NOTIFY_SECRET", "")
bot_link_api_base_url = os.getenv("BOT_LINK_API_BASE_URL", os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000")).rstrip("/")
bot_link_reminder_enabled = os.getenv("BOT_LINK_REMINDER_ENABLED", "1").strip().lower() not in {"0", "false", "no", "off"}
bot_link_reminder_interval_seconds = int(os.getenv("BOT_LINK_REMINDER_INTERVAL_SECONDS", "21600") or 21600)
bot_link_reminder_cooldown_seconds = int(os.getenv("BOT_LINK_REMINDER_COOLDOWN_SECONDS", "86400") or 86400)
bot_link_reminder_initial_delay_seconds = int(os.getenv("BOT_LINK_REMINDER_INITIAL_DELAY_SECONDS", "60") or 60)
bot_link_reminder_task: asyncio.Task | None = None
JOB_REDIRECT_URL_RE = re.compile(r"(https://bottimviec\.ai/jobs/redirect\?[^\s)]+|/jobs/redirect\?[^\s)]+)")
TELEGRAM_JOB_LINK_LINE_RE = re.compile(r"(?m)^(\s*-?\s*)Xem chi tiết(?:\s*/\s*Ứng tuyển)?\s*:\s*(https?://[^\s)]+|/jobs/redirect\?[^\s)]+)\s*$")
TELEGRAM_JOB_MARKDOWN_LINK_RE = re.compile(r"\[Xem chi tiết(?:\s*/\s*Ứng tuyển)?\]\(([^)]+)\)")
BOT_LINK_CODE_RE = re.compile(r"\b[A-Z0-9]{4}(?:-| )?[A-Z0-9]{4}\b", re.IGNORECASE)

@app.get("/")
async def root():
    return {"message": "AI Chatbot Backend is running!"}


@app.on_event("startup")
async def start_bot_link_reminder_scheduler():
    global bot_link_reminder_task
    if not bot_link_reminder_enabled:
        logger.info("Bot link reminder scheduler disabled")
        return
    if bot_link_reminder_task and not bot_link_reminder_task.done():
        return
    bot_link_reminder_task = asyncio.create_task(bot_link_reminder_loop())
    logger.info(
        "Bot link reminder scheduler started interval_seconds=%s cooldown_seconds=%s initial_delay_seconds=%s",
        bot_link_reminder_interval_seconds,
        bot_link_reminder_cooldown_seconds,
        bot_link_reminder_initial_delay_seconds,
    )


@app.on_event("shutdown")
async def stop_bot_link_reminder_scheduler():
    global bot_link_reminder_task
    if bot_link_reminder_task and not bot_link_reminder_task.done():
        bot_link_reminder_task.cancel()
        try:
            await bot_link_reminder_task
        except asyncio.CancelledError:
            pass
    bot_link_reminder_task = None

# Initialize Zalo Manager
zalo_bot_token = os.getenv("ZALO_BOT_TOKEN")
zalo_app_id = os.getenv("ZALO_APP_ID")
zalo_app_secret = os.getenv("ZALO_APP_SECRET")
if zalo_bot_token:
    zalo_manager = ZaloManager(bot_token=zalo_bot_token)
elif zalo_app_id and zalo_app_secret:
    zalo_manager = ZaloManager(zalo_app_id, zalo_app_secret)
else:
    zalo_manager = None


def add_bot_tracking_to_job_redirects(
    text: str,
    *,
    channel: str,
    chat_id: str,
    conversation_id: str,
) -> str:
    def replace(match: re.Match[str]) -> str:
        url = match.group(1)
        parts = urlsplit(url)
        params = dict(parse_qsl(parts.query, keep_blank_values=True))
        params.setdefault("channel", channel)
        params.setdefault("chat_id", str(chat_id))
        params.setdefault("conversation_id", conversation_id)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(params), parts.fragment))

    return JOB_REDIRECT_URL_RE.sub(replace, text)


def compact_telegram_job_links(text: str) -> str:
    text = TELEGRAM_JOB_LINK_LINE_RE.sub(
        lambda match: f"{match.group(1)}[Xem chi tiết/Ứng tuyển]({match.group(2)})",
        text,
    )
    return TELEGRAM_JOB_MARKDOWN_LINK_RE.sub(
        lambda match: f"[Xem chi tiết/Ứng tuyển]({match.group(1)})",
        text,
    )


def _bot_link_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if bot_notify_secret:
        headers["x-bot-notify-secret"] = bot_notify_secret
    return headers


async def lookup_bot_account(*, channel: str, chat_id: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            f"{bot_link_api_base_url}/api/v1/internal/bot-links/lookup",
            headers=_bot_link_headers(),
            json={"channel": channel, "chat_id": str(chat_id)},
        )
        response.raise_for_status()
        return response.json()


async def verify_bot_link_code(
    *,
    code: str,
    channel: str,
    chat_id: str,
    display_name: str | None = None,
    username: str | None = None,
) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            f"{bot_link_api_base_url}/api/v1/internal/bot-links/verify",
            headers=_bot_link_headers(),
            json={
                "code": code,
                "channel": channel,
                "chat_id": str(chat_id),
                "display_name": display_name,
                "username": username,
            },
        )
        response.raise_for_status()
        return response.json()


async def list_linked_bot_recipients() -> dict[str, list[str]]:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            f"{bot_link_api_base_url}/api/v1/internal/bot-links/recipients",
            headers=_bot_link_headers(),
        )
        response.raise_for_status()
        payload = response.json()
        return {
            "telegram": [str(item) for item in payload.get("telegram", []) if str(item).strip()],
            "zalo": [str(item) for item in payload.get("zalo", []) if str(item).strip()],
        }


def bot_link_instruction_text() -> str:
    return (
        "Để nhận thông báo việc làm mỗi ngày, tôi cần định danh bạn.\n"
        "Hãy vào https://bottimviec.ai, bấm biểu tượng Zalo/Telegram cạnh ô chat, "
        "copy mã định danh và gửi lại mã đó cho bot."
    )


def normalize_bot_link_message(text: str) -> str:
    return text.replace("\u2013", "-").replace("\u2014", "-")


def format_link_success_text(payload: dict) -> str:
    user = payload.get("user") if isinstance(payload.get("user"), dict) else {}
    lines = [
        "Cảm ơn bạn đã định danh.",
        "",
        "Thông tin của bạn:",
        f"- Tài khoản: {user.get('name') or user.get('username') or 'Chưa rõ'}",
    ]
    if user.get("email"):
        lines.append(f"- Email: {user['email']}")
    if user.get("current_location_address"):
        lines.append(f"- Vị trí: {user['current_location_address']}")
    lines.append("")
    lines.append("Bạn sẽ nhận được thông báo khi có việc làm mới.")
    return "\n".join(lines)


async def send_platform_text(*, platform: str, chat_id: str, text: str) -> None:
    if platform == "tele":
        sender = TelegramSender()
        try:
            await sender.send_message(chat_id, text, text_mode=None)
        finally:
            sender.close()
        return
    if platform == "zalo":
        if zalo_manager:
            await zalo_manager.send_zalo_message(chat_id, text)
        else:
            logger.error("Cannot send Zalo message: ZaloManager is not initialized.")


async def send_bot_link_reminders_to_unknown_chats(*, respect_cooldown: bool = True) -> dict:
    ai_integration = await get_ai_integration()
    recipients = ai_integration.list_known_chat_ids()
    sent = {"telegram": 0, "zalo": 0}
    skipped_linked = {"telegram": 0, "zalo": 0}
    skipped_cooldown = {"telegram": 0, "zalo": 0}
    failed = {"telegram": 0, "zalo": 0}

    for platform, channel, chat_ids in [
        ("tele", "telegram", recipients.get("telegram", [])),
        ("zalo", "zalo", recipients.get("zalo", [])),
    ]:
        for chat_id in chat_ids:
            try:
                account = await lookup_bot_account(channel=channel, chat_id=chat_id)
                if account.get("linked"):
                    skipped_linked[channel] += 1
                    continue
                if respect_cooldown and not ai_integration.should_send_bot_link_reminder(
                    channel=channel,
                    chat_id=chat_id,
                    cooldown_seconds=bot_link_reminder_cooldown_seconds,
                ):
                    skipped_cooldown[channel] += 1
                    continue
                await send_platform_text(platform=platform, chat_id=chat_id, text=bot_link_instruction_text())
                ai_integration.mark_bot_link_reminder_sent(channel=channel, chat_id=chat_id)
                sent[channel] += 1
            except Exception as exc:
                failed[channel] += 1
                logger.error(f"Failed to send bot link reminder to {channel}:{chat_id}: {exc}")

    return {
        "sent": sent,
        "skipped_linked": skipped_linked,
        "skipped_cooldown": skipped_cooldown,
        "failed": failed,
    }


async def bot_link_reminder_loop() -> None:
    await asyncio.sleep(max(0, bot_link_reminder_initial_delay_seconds))
    while True:
        try:
            result = await send_bot_link_reminders_to_unknown_chats(respect_cooldown=True)
            logger.info(f"bot_link_reminder_tick result={result}")
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error(f"bot_link_reminder_tick_failed: {exc}")
        await asyncio.sleep(max(60, bot_link_reminder_interval_seconds))

# ============ Example Handlers ============

async def example_1(sender: TelegramSender, chat_id: str):
    """Example 1: Send a simple message"""
    logger.info("Running Example 1: Simple text message")
    result = await sender.send_message(
        to=chat_id,
        text="Hello! This is Example 1 - a simple test message.",
        silent=False,
        text_mode="markdown"
    )
    return result

async def example_2(sender: TelegramSender, chat_id: str):
    """Example 2: Send message with retry config"""
    logger.info("Running Example 2: Message with retry config")
    retry_config = RetryConfig(max_attempts=5, backoff=1.5, initial_delay=0.3)
    result = await sender.send_message(
        to=chat_id,
        text="This is Example 2 - Message with retry configuration",
        retry=retry_config
    )
    return result

async def example_3(sender: TelegramSender, chat_id: str):
    """Example 3: Send message with inline buttons"""
    logger.info("Running Example 3: Message with inline buttons")
    buttons = [
        [
            {"text": "Python", "callback_data": "lang_python"},
            {"text": "JavaScript", "callback_data": "lang_js"}
        ],
        [
            {"text": "Go", "callback_data": "lang_go"},
            {"text": "Rust", "callback_data": "lang_rust"}
        ]
    ]
    result = await sender.send_message(
        to=chat_id,
        text="Example 3: Choose your favorite programming language:",
        buttons=buttons
    )
    return result

async def example_4(sender: TelegramSender, chat_id: str):
    """Example 4: Send HTML formatted message"""
    logger.info("Running Example 4: HTML formatted message")
    html_text = """<b>Example 4 - Bold text</b>
<i>Italic text</i>
<code>code</code>
<a href="https://example.com">Link to example</a>"""
    result = await sender.send_message(
        to=chat_id,
        text=html_text,
        text_mode="html"
    )
    return result

async def example_5(sender: TelegramSender, chat_id: str):
    """Example 5: Send typing indicator"""
    logger.info("Running Example 5: Typing indicator")
    result = await sender.send_typing(to=chat_id)
    await asyncio.sleep(2)
    # Send follow-up message
    result = await sender.send_message(
        to=chat_id,
        text="Example 5: I was typing... done! 👍"
    )
    return result

async def example_6(sender: TelegramSender, chat_id: str):
    """Example 6: Send poll"""
    logger.info("Running Example 6: Send poll")
    poll_data = {
        "question": "Example 6: What's your favorite Python version?",
        "options": ["3.8", "3.9", "3.10", "3.11", "3.12"],
        "poll_type": "regular",
        "is_anonymous": True,
        "allows_multiple_answers": False
    }
    result = await sender.send_poll(to=chat_id, poll_data=poll_data)
    return result

async def example_7(sender: TelegramSender, chat_id: str):
    """Example 7: Send and edit message"""
    logger.info("Running Example 7: Send and edit message")
    # Send original message
    send_result = await sender.send_message(
        to=chat_id,
        text="Example 7: Original message (will be edited)"
    )
    if send_result.get("ok"):
        await asyncio.sleep(1)
        # Edit the message
        edit_result = await sender.edit_message(
            chat_id=chat_id,
            message_id=send_result["message_id"],
            text="**Example 7: Edited message** with updated content! ✏️"
        )
        return edit_result
    return send_result

async def example_8(sender: TelegramSender, chat_id: str):
    """Example 8: Send and pin message"""
    logger.info("Running Example 8: Send and pin message")
    # Send message
    send_result = await sender.send_message(
        to=chat_id,
        text="Example 8: This message will be pinned! 📌"
    )
    if send_result.get("ok"):
        await asyncio.sleep(1)
        # Pin the message
        pin_result = await sender.pin_message(
            chat_id=chat_id,
            message_id=send_result["message_id"]
        )
        return pin_result
    return send_result

async def example_9(sender: TelegramSender, chat_id: str):
    """Example 9: Send and react to message"""
    logger.info("Running Example 9: Send and react to message")
    # Send message
    send_result = await sender.send_message(
        to=chat_id,
        text="Example 9: React to this message with 👍"
    )
    if send_result.get("ok"):
        await asyncio.sleep(1)
        # React with emoji
        react_result = await sender.react_message(
            chat_id=chat_id,
            message_id=send_result["message_id"],
            emoji="👍"
        )
        return react_result
    return send_result

async def example_10(sender: TelegramSender, chat_id: str):
    """Example 10: Send message with reply buttons and silent mode"""
    logger.info("Running Example 10: Message with buttons and silent mode")
    buttons = [
        [
            {"text": "✅ Yes", "callback_data": "yes_action"},
            {"text": "❌ No", "callback_data": "no_action"}
        ]
    ]
    result = await sender.send_message(
        to=chat_id,
        text="Example 10: Do you like these examples? (silent message)",
        buttons=buttons,
        silent=True
    )
    return result

async def example_11(sender: TelegramSender, chat_id: str):
    """Example 11: Send, pin, and unpin message"""
    logger.info("Running Example 11: Pin and unpin message")
    # Send message
    send_result = await sender.send_message(
        to=chat_id,
        text="Example 11: This message will be pinned and then unpinned! 📌➡️📍"
    )
    if send_result.get("ok"):
        await asyncio.sleep(1)
        # Pin the message
        pin_result = await sender.pin_message(
            chat_id=chat_id,
            message_id=send_result["message_id"]
        )
        await asyncio.sleep(2)
        # Unpin the message
        unpin_result = await sender.unpin_message(
            chat_id=chat_id,
            message_id=send_result["message_id"]
        )
        return unpin_result
    return send_result

async def example_12(sender: TelegramSender, chat_id: str):
    """Example 12: Send message and edit reply markup"""
    logger.info("Running Example 12: Edit message reply markup")
    # Send message with initial buttons
    initial_buttons = [
        [
            {"text": "Option A", "callback_data": "option_a"},
            {"text": "Option B", "callback_data": "option_b"}
        ]
    ]
    send_result = await sender.send_message(
        to=chat_id,
        text="Example 12: Choose an option (buttons will change):",
        buttons=initial_buttons
    )
    if send_result.get("ok"):
        await asyncio.sleep(2)
        # Edit buttons
        new_buttons = [
            [
                {"text": "✅ Confirm", "callback_data": "confirm"},
                {"text": "❌ Cancel", "callback_data": "cancel"}
            ]
        ]
        edit_result = await sender.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=send_result["message_id"],
            buttons=new_buttons
        )
        return edit_result
    return send_result

async def example_13(sender: TelegramSender, chat_id: str):
    """Example 13: Create forum topic"""
    logger.info("Running Example 13: Create forum topic")
    try:
        result = await sender.create_forum_topic(
            chat_id=chat_id,
            name="Example Topic 13",
            icon_color=7322096  # Blue color
        )
        return result
    except Exception as e:
        # Fallback: send message explaining forum topics need supergroups
        return await sender.send_message(
            to=chat_id,
            text="Example 13: Forum topics require supergroups. This example would create a topic named 'Example Topic 13' with blue icon."
        )

async def example_14(sender: TelegramSender, chat_id: str):
    """Example 14: Send and delete message"""
    logger.info("Running Example 14: Send and delete message")
    # Send message
    send_result = await sender.send_message(
        to=chat_id,
        text="Example 14: This message will be deleted in 3 seconds... ⏰"
    )
    if send_result.get("ok"):
        await asyncio.sleep(3)
        # Delete the message
        delete_result = await sender.delete_message(
            chat_id=chat_id,
            message_id=send_result["message_id"]
        )
        return delete_result
    return send_result

async def example_help(sender: TelegramSender, chat_id: str):
    """Show available examples"""
    logger.info("Showing help message")
    help_text = """📚 **Available Examples:**

Send any of these commands to test:
• Example 1 - Simple text message
• Example 2 - Message with retry config
• Example 3 - Message with buttons
• Example 4 - HTML formatted message
• Example 5 - Typing indicator
• Example 6 - Poll
• Example 7 - Edit message
• Example 8 - Pin message
• Example 9 - React to message
• Example 10 - Buttons with silent mode
• Example 11 - Pin and unpin message
• Example 12 - Edit reply markup
• Example 13 - Create forum topic
• Example 14 - Send and delete message

Just send the example name (e.g., "Example 1")"""
    """Show available examples"""
    logger.info("Showing help message")
    help_text = """📚 **Available Examples:**

Send any of these commands to test:
• Example 1 - Simple text message
• Example 2 - Message with retry config
• Example 3 - Message with buttons
• Example 4 - HTML formatted message
• Example 5 - Typing indicator
• Example 6 - Poll
• Example 7 - Edit message
• Example 8 - Pin message
• Example 9 - React to message
• Example 10 - Buttons with silent mode

Just send the example name (e.g., "Example 1")"""
    
    result = await sender.send_message(
        to=chat_id,
        text=help_text,
        text_mode="markdown"
    )
    return result

# Map examples to handlers
EXAMPLES = {
    "example 1": example_1,
    "example 2": example_2,
    "example 3": example_3,
    "example 4": example_4,
    "example 5": example_5,
    "example 6": example_6,
    "example 7": example_7,
    "example 8": example_8,
    "example 9": example_9,
    "example 10": example_10,
    "example 11": example_11,
    "example 12": example_12,
    "example 13": example_13,
    "example 14": example_14,
    "help": example_help,
}

async def process_with_ai(msg: IncomingMessage):
    """Process incoming message - check if it's an example command or use AI agent"""
    logger.info(f"Processing message from {msg.platform} ({msg.message_type}): {msg.text_content}")

    # Check if message is an example command
    command = msg.text_content.strip().lower()
    channel = "telegram" if msg.platform == "tele" else msg.platform
    linked_user = None

    if channel in {"telegram", "zalo"}:
        code_match = BOT_LINK_CODE_RE.search(normalize_bot_link_message(msg.text_content.strip()))
        if code_match:
            logger.info(f"Detected bot link code from {channel}:{msg.user_id}")
            try:
                verify_result = await verify_bot_link_code(
                    code=code_match.group(0),
                    channel=channel,
                    chat_id=msg.user_id,
                )
                text = (
                    format_link_success_text(verify_result)
                    if verify_result.get("ok")
                    else verify_result.get("message", "Mã định danh không hợp lệ")
                )
            except Exception as exc:
                logger.error(f"Bot link verify failed for {channel}:{msg.user_id}: {exc}")
                text = "Không thể xác thực mã lúc này. Vui lòng thử lại sau."
            await send_platform_text(platform=msg.platform, chat_id=msg.user_id, text=text)
            return

        try:
            account = await lookup_bot_account(channel=channel, chat_id=msg.user_id)
        except Exception as exc:
            logger.error(f"Bot link lookup failed for {channel}:{msg.user_id}: {exc}")
            await send_platform_text(platform=msg.platform, chat_id=msg.user_id, text=bot_link_instruction_text())
            return
        linked_user = account.get("user") if isinstance(account.get("user"), dict) else None

        if not account.get("linked"):
            await send_platform_text(platform=msg.platform, chat_id=msg.user_id, text=bot_link_instruction_text())
            return

    if msg.platform == "tele":
        try:
            sender = TelegramSender()

            # Handle callback queries (button clicks)
            if msg.message_type == "callback_query":
                logger.info(f"Received callback query: {command}")
                # For now, treat callback data as potential commands
                # You might want to handle this differently in production

            # Check if it's an example command
            if command in EXAMPLES:
                logger.info(f"Running example: {command}")
                result = await EXAMPLES[command](sender, msg.user_id)
                if result.get("ok"):
                    logger.info(f"Example {command} executed successfully: {result}")
                else:
                    logger.error(f"Example failed: {result.get('error')}")
            else:
                # Use AI agent for regular messages
                logger.info(f"[AI Agent] Getting response for user {msg.user_id}: {msg.text_content}")
                
                try:
                    ai_integration = await get_ai_integration()
                    conversation_id = f"telegram:{msg.user_id}"
                    internal_user_id = f"user_{linked_user['id']}" if linked_user and linked_user.get("id") else None
                    ai_integration.ensure_telegram_user(str(msg.user_id), internal_user_id=internal_user_id)
                    ai_integration.ensure_conversation(conversation_id, str(msg.user_id))
                    ai_integration.add_message(conversation_id, "user", msg.text_content, message_type=msg.message_type or "text")

                    history = ai_integration.load_conversation_history(conversation_id)
                    response_text, events = await ai_integration.run_turn(
                        conversation_uuid=conversation_id,
                        run_uuid=uuid4().hex[:12],
                        user_id=internal_user_id or str(msg.user_id),
                        messages=history,
                        metadata={
                            "user_profile": {
                                **(linked_user or {}),
                                "channel": "telegram",
                                "telegram_chat_id": str(msg.user_id),
                            }
                        },
                    )
                    response_text = add_bot_tracking_to_job_redirects(
                        response_text,
                        channel="telegram",
                        chat_id=msg.user_id,
                        conversation_id=conversation_id,
                    )
                    response_text = compact_telegram_job_links(response_text)

                    logger.info(f"[AI Agent] Response: {response_text[:100]}...")
                    
                    if len(response_text) > 4090:
                        chunks = []
                        current_chunk = ""
                        for line in response_text.split('\n'):
                            if len(current_chunk) + len(line) + 1 > 4090:
                                if current_chunk:
                                    chunks.append(current_chunk)
                                current_chunk = line
                            else:
                                current_chunk += ('\n' if current_chunk else '') + line
                        if current_chunk:
                            chunks.append(current_chunk)

                        for i, chunk in enumerate(chunks):
                            result = await sender.send_message(
                                msg.user_id,
                                chunk,
                                text_mode="html"
                            )
                            if not result.get("ok"):
                                logger.error(f"Failed to send chunk {i+1}/{len(chunks)}: {result.get('error')}")
                            else:
                                logger.info(f"Chunk {i+1}/{len(chunks)} sent successfully")
                            await asyncio.sleep(0.2)
                    else:
                        result = await sender.send_message(
                            msg.user_id,
                            response_text,
                            text_mode="html"
                        )
                        if result.get("ok"):
                            logger.info(f"AI message sent to Telegram successfully")
                        else:
                            logger.error(f"Failed to send AI message: {result.get('error')}")
                
                except Exception as e:
                    logger.error(f"Error getting AI response: {str(e)}")
                    fallback_text = f"❌ Error from AI agent: {str(e)[:100]}\n\nSend 'help' to see available examples."
                    result = await sender.send_message(msg.user_id, fallback_text, text_mode=None)
                    logger.info(f"Fallback message sent: {result}")

            sender.close()
        except Exception as e:
            logger.error(f"Error processing Telegram message: {str(e)}")
    
    elif msg.platform == "zalo":
        try:
            logger.info(f"[AI Agent][Zalo] Getting response for user {msg.user_id}: {msg.text_content}")
            ai_integration = await get_ai_integration()
            conversation_id = f"zalo:{msg.user_id}"
            internal_user_id = f"user_{linked_user['id']}" if linked_user and linked_user.get("id") else f"zalo_{msg.user_id}"
            ai_integration.ensure_telegram_user(f"zalo:{msg.user_id}", internal_user_id=internal_user_id)
            ai_integration.ensure_conversation(conversation_id, f"zalo:{msg.user_id}")
            ai_integration.add_message(conversation_id, "user", msg.text_content, message_type=msg.message_type or "text")

            history = ai_integration.load_conversation_history(conversation_id)
            response_text, events = await ai_integration.run_turn(
                conversation_uuid=conversation_id,
                run_uuid=uuid4().hex[:12],
                user_id=internal_user_id,
                messages=history,
                metadata={
                    "user_profile": {
                        **(linked_user or {}),
                        "channel": "zalo",
                        "zalo_user_id": str(msg.user_id),
                    }
                },
            )
            response_text = add_bot_tracking_to_job_redirects(
                response_text,
                channel="zalo",
                chat_id=msg.user_id,
                conversation_id=conversation_id,
            )
            logger.info(f"[AI Agent][Zalo] Response: {response_text[:100]}...")
            if not zalo_manager:
                logger.error("Cannot send Zalo response: ZaloManager is not initialized. Check ZALO_BOT_TOKEN.")
                return
            send_result = await zalo_manager.send_zalo_message(msg.user_id, response_text)
            logger.info(f"Message sent to Zalo chat_id={msg.user_id}, result={send_result}")
        except Exception as e:
            logger.error(f"Error processing Zalo message: {str(e)}")

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()

    # Handle different types of Telegram updates
    if 'callback_query' in data:
        # Handle button clicks
        callback = data['callback_query']
        chat_id = str(callback['message']['chat']['id'])
        text = callback['data']  # The callback_data from the button
        user_id = str(callback['from']['id'])

        msg = IncomingMessage(
            user_id=user_id,
            text_content=text,
            platform="tele",
            message_type="callback_query"
        )

    elif 'message' in data:
        # Handle regular messages
        message = data['message']
        chat_id = str(message['chat']['id'])
        user_id = chat_id

        # Extract text content from different message types
        message_type = "text"
        if 'text' in message:
            text = message['text']
        elif 'sticker' in message:
            text = f"[Sticker: {message['sticker'].get('emoji', 'sticker')}]"
            message_type = "sticker"
        elif 'photo' in message:
            text = "[Photo]"
            message_type = "photo"
        elif 'video' in message:
            text = "[Video]"
            message_type = "video"
        elif 'document' in message:
            text = f"[Document: {message['document'].get('file_name', 'file')}]"
            message_type = "document"
        elif 'audio' in message:
            text = f"[Audio: {message['audio'].get('title', 'audio')}]"
            message_type = "audio"
        elif 'voice' in message:
            text = "[Voice message]"
            message_type = "voice"
        elif 'poll' in message:
            text = f"[Poll: {message['poll']['question']}]"
            message_type = "poll"
        else:
            text = "[Unsupported message type]"
            message_type = "unsupported"

        msg = IncomingMessage(
            user_id=user_id,
            text_content=text,
            platform="tele",
            message_type=message_type
        )

    elif 'edited_message' in data:
        # Handle edited messages
        message = data['edited_message']
        chat_id = str(message['chat']['id'])
        user_id = chat_id

        if 'text' in message:
            text = message['text']
            message_type = "edited_text"
        else:
            text = "[Edited non-text message]"
            message_type = "edited_other"

        msg = IncomingMessage(
            user_id=user_id,
            text_content=text,
            platform="tele",
            message_type=message_type
        )

    else:
        # Unknown update type
        logger.warning(f"Unknown Telegram update type: {list(data.keys())}")
        return {"status": "ignored"}

    # Process the message
    await process_with_ai(msg)
    return {"status": "ok"}

@app.post("/webhook/zalo")
async def zalo_webhook(request: Request):
    data = await request.json()
    parsed = _parse_zalo_webhook_payload(data)
    if parsed is None:
        logger.info(
            "Ignored Zalo webhook event: "
            f"event={data.get('event_name') or data.get('event')}, "
            f"payload={_compact_json(data)}"
        )
        return {"status": "ignored"}

    user_id, text, message_type = parsed
    logger.info(
        "Parsed Zalo webhook: "
        f"user_id={user_id}, message_type={message_type}, text_preview={text[:120]!r}, payload={_compact_json(data)}"
    )
    msg = IncomingMessage(user_id=user_id, text_content=text, platform="zalo", message_type=message_type)
    await process_with_ai(msg)
    return {"status": "ok"}


@app.post("/internal/job-notifications")
async def internal_job_notification(request: Request):
    if bot_notify_secret:
        received_secret = request.headers.get("x-bot-notify-secret", "")
        if received_secret != bot_notify_secret:
            raise HTTPException(status_code=401, detail="Invalid notification secret")

    payload = await request.json()
    job = payload.get("job") if isinstance(payload.get("job"), dict) else {}
    try:
        recipients = await list_linked_bot_recipients()
    except Exception as exc:
        logger.error(f"Failed to fetch linked bot recipients: {exc}")
        recipients = {"telegram": [], "zalo": []}

    telegram_sent = 0
    telegram_failed = 0
    zalo_sent = 0
    zalo_failed = 0

    telegram_ids = recipients.get("telegram", [])
    if telegram_ids:
        sender = TelegramSender()
        try:
            for chat_id in telegram_ids:
                user_name = await get_linked_user_display_name(channel="telegram", chat_id=chat_id)
                text = _format_job_notification(
                    job,
                    channel="telegram",
                    chat_id=chat_id,
                    conversation_id=f"telegram:{chat_id}",
                    user_name=user_name,
                )
                text = compact_telegram_job_links(text)
                result = await sender.send_message(chat_id, text, text_mode="html")
                if result.get("ok"):
                    telegram_sent += 1
                else:
                    telegram_failed += 1
                    logger.error(f"Failed to send Telegram job notification to {chat_id}: {result}")
        finally:
            sender.close()

    if zalo_manager:
        for chat_id in recipients.get("zalo", []):
            try:
                user_name = await get_linked_user_display_name(channel="zalo", chat_id=chat_id)
                text = _format_job_notification(
                    job,
                    channel="zalo",
                    chat_id=chat_id,
                    conversation_id=f"zalo:{chat_id}",
                    user_name=user_name,
                )
                result = await zalo_manager.send_zalo_message(chat_id, text)
                if result.get("ok"):
                    zalo_sent += 1
                else:
                    zalo_failed += 1
                    logger.error(f"Failed to send Zalo job notification to {chat_id}: {result}")
            except Exception as exc:
                zalo_failed += 1
                logger.error(f"Failed to send Zalo job notification to {chat_id}: {exc}")
    elif recipients.get("zalo"):
        zalo_failed = len(recipients.get("zalo", []))
        logger.error("Cannot send Zalo job notifications: ZaloManager is not initialized.")

    return {
        "status": "ok",
        "telegram_sent": telegram_sent,
        "telegram_failed": telegram_failed,
        "zalo_sent": zalo_sent,
        "zalo_failed": zalo_failed,
    }


@app.post("/internal/bot-link-reminders")
async def internal_bot_link_reminders(request: Request):
    if bot_notify_secret:
        received_secret = request.headers.get("x-bot-notify-secret", "")
        if received_secret != bot_notify_secret:
            raise HTTPException(status_code=401, detail="Invalid notification secret")

    result = await send_bot_link_reminders_to_unknown_chats(respect_cooldown=False)
    return {"status": "ok", **result}


@app.post("/internal/dispatch-message")
async def internal_dispatch_message(request: Request):
    """
    Nhận DispatchAction từ SmartDispatcher và gửi tin cho user cụ thể.

    Payload JSON:
    {
        "channel": "telegram" | "zalo",
        "chat_id": "123456789",
        "user_id": 42,
        "user_name": "Hùng",
        "message_text": "...",
        "message_type": "single" | "digest" | "cold_start",
        "job_ids": ["job-1", "job-2"],
        "match_scores": [0.85, 0.72]
    }
    """
    if bot_notify_secret:
        received_secret = request.headers.get("x-bot-notify-secret", "")
        if received_secret != bot_notify_secret:
            raise HTTPException(status_code=401, detail="Invalid notification secret")

    payload = await request.json()
    channel = str(payload.get("channel", "")).strip().lower()
    chat_id = str(payload.get("chat_id", "")).strip()
    message_text = str(payload.get("message_text", "")).strip()
    message_type = str(payload.get("message_type", "single")).strip()
    user_name = str(payload.get("user_name", "")).strip()

    if not channel or not chat_id or not message_text:
        raise HTTPException(
            status_code=400,
            detail="Missing required fields: channel, chat_id, message_text",
        )

    logger.info(
        "dispatch_message_received channel=%s chat_id=%s type=%s user=%s len=%d",
        channel, chat_id, message_type, user_name, len(message_text),
    )

    result = {"channel": channel, "chat_id": chat_id, "type": message_type}

    try:
        if channel == "telegram":
            sender = TelegramSender()
            try:
                # Compact links cho Telegram
                formatted_text = compact_telegram_job_links(message_text)
                send_result = await sender.send_message(
                    chat_id, formatted_text, text_mode="html",
                )
                result["ok"] = send_result.get("ok", False)
                if not send_result.get("ok"):
                    result["error"] = send_result.get("error", "Unknown error")
                    logger.error(
                        "dispatch_send_failed channel=telegram chat_id=%s error=%s",
                        chat_id, result["error"],
                    )
            finally:
                sender.close()

        elif channel == "zalo":
            if not zalo_manager:
                result["ok"] = False
                result["error"] = "ZaloManager not initialized"
                logger.error("dispatch_send_failed channel=zalo reason=no_zalo_manager")
            else:
                send_result = await zalo_manager.send_zalo_message(chat_id, message_text)
                result["ok"] = send_result.get("ok", False) if isinstance(send_result, dict) else True
                if isinstance(send_result, dict) and not send_result.get("ok"):
                    result["error"] = send_result.get("error", "Unknown error")

        else:
            result["ok"] = False
            result["error"] = f"Unsupported channel: {channel}"

    except Exception as exc:
        result["ok"] = False
        result["error"] = str(exc)
        logger.error(
            "dispatch_send_exception channel=%s chat_id=%s error=%s",
            channel, chat_id, exc,
        )

    logger.info("dispatch_message_result %s", result)
    return {"status": "ok" if result.get("ok") else "error", **result}



def _parse_zalo_webhook_payload(data: dict) -> tuple[str, str, str] | None:
    """Extract a user text message from common Zalo OA webhook payload shapes."""
    sender = data.get("sender") if isinstance(data.get("sender"), dict) else {}
    message = data.get("message") if isinstance(data.get("message"), dict) else {}
    message_sender = message.get("sender") if isinstance(message.get("sender"), dict) else {}
    message_from = message.get("from") if isinstance(message.get("from"), dict) else {}
    message_chat = message.get("chat") if isinstance(message.get("chat"), dict) else {}

    user_id = (
        message_chat.get("id")
        or sender.get("id")
        or sender.get("user_id")
        or message_sender.get("id")
        or message_sender.get("user_id")
        or message_from.get("id")
        or message_from.get("user_id")
        or message.get("from_id")
        or message.get("user_id")
        or message.get("uid")
        or message.get("sender_id")
        or data.get("user_id")
        or data.get("from_user_id")
        or data.get("uid")
    )
    text = (
        message.get("text")
        or message.get("content")
        or message.get("message")
        or data.get("text")
        or data.get("message_text")
        or data.get("content")
    )

    if not text and isinstance(message.get("attachments"), list) and message["attachments"]:
        text = "[Zalo attachment]"

    if not user_id or not text:
        return None

    message_type = str(data.get("event_name") or data.get("event") or "zalo_message")
    return str(user_id), str(text), message_type


async def get_linked_user_display_name(*, channel: str, chat_id: str) -> str:
    try:
        account = await lookup_bot_account(channel=channel, chat_id=chat_id)
    except Exception as exc:
        logger.error(f"Failed to lookup linked user for notification {channel}:{chat_id}: {exc}")
        return ""
    user = account.get("user") if isinstance(account.get("user"), dict) else {}
    return _friendly_user_name(str(user.get("name") or user.get("username") or "").strip())


def _friendly_user_name(value: str) -> str:
    if not value:
        return ""
    clean = " ".join(value.replace("@", " ").split())
    if not clean:
        return ""
    parts = clean.split()
    if len(parts) >= 2 and len(parts[-1]) > 1 and parts[-1].isupper():
        return parts[0][:30]
    # Vietnamese users are commonly addressed by their given name, often the last token.
    return parts[-1][:30]


def _notification_intro(*, user_name: str, job: dict, chat_id: str) -> str:
    title = str(job.get("title") or "").strip()
    company = str(job.get("company") or "").strip()
    name = user_name or "bạn"
    variants = [
        f"{name} ơi, việc làm này có hợp với bạn không?",
        f"{name} ơi, mình vừa thấy một job mới khá đáng xem.",
        f"{name} ơi, job này có thể là một cơ hội tốt cho bạn.",
        f"{name} ơi, có một việc mới vừa được thêm vào hệ thống.",
        f"{name} ơi, thử xem job này có đúng gu của bạn không.",
        f"{name} ơi, mình nghĩ job này đáng để bạn lướt qua.",
        f"{name} ơi, có tin tuyển dụng mới cho bạn đây.",
        f"{name} ơi, job mới này có vẻ đáng chú ý.",
        f"{name} ơi, bạn muốn xem thử cơ hội này không?",
        f"{name} ơi, có một job mới vừa lên, xem nhanh nhé.",
    ]
    if title and company:
        variants.extend(
            [
                f"{name} ơi, {company} đang tuyển {title}. Bạn xem thử nhé.",
                f"{name} ơi, có job {title} ở {company}, nghe khá đáng chú ý.",
                f"{name} ơi, mình thấy {company} vừa có vị trí {title}.",
            ]
        )
    seed = f"{chat_id}|{job.get('id') or job.get('job_id') or job.get('job_url') or title}|{company}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    index = int(digest[:8], 16) % len(variants)
    return variants[index]


def _format_job_notification(
    job: dict,
    *,
    channel: str,
    chat_id: str,
    conversation_id: str,
    user_name: str = "",
) -> str:
    title = str(job.get("title") or "Job mới").strip()
    company = str(job.get("company") or "").strip()
    location = str(job.get("location") or job.get("location_norm") or "").strip()
    salary = str(job.get("salary_text") or "Thương lượng").strip()
    source = str(job.get("source") or "").strip()
    highlight = _job_notification_highlight(job, location)
    url = _build_job_notification_redirect_url(
        job,
        channel=channel,
        chat_id=chat_id,
        conversation_id=conversation_id,
    )

    heading = f"### {company} - {title}" if company else f"### {title}"
    lines = [_notification_intro(user_name=user_name, job=job, chat_id=chat_id), "", heading, f"- Mức lương: {salary}"]
    if location:
        lines.append(f"- Địa điểm: {location}")
    if source:
        lines.append(f"- Nguồn: {source}")
    if highlight:
        lines.append(f"- Điểm nổi bật: {highlight}")
    if url:
        lines.append(f"- Xem chi tiết: {url}")
    return "\n".join(lines)


def _job_notification_highlight(job: dict, location: str) -> str:
    text = str(
        job.get("summary")
        or job.get("description")
        or job.get("requirement")
        or ""
    ).strip()
    if not text and location:
        text = f"Địa điểm: {location}."
    text = " ".join(text.split())
    if len(text) > 320:
        return text[:317].rstrip() + "..."
    return text


def _build_job_notification_redirect_url(
    job: dict,
    *,
    channel: str,
    chat_id: str,
    conversation_id: str,
) -> str:
    target = str(job.get("job_url") or job.get("url") or "").strip()
    if not target:
        return ""

    source = str(job.get("source") or "").strip() or _infer_job_source_from_url(target)
    params = {
        "job_id": str(job.get("id") or job.get("job_id") or job.get("job_id_vnw") or "").strip(),
        "source": _normalize_job_source(source),
        "target": target,
        "title": str(job.get("title") or ""),
        "company": str(job.get("company") or ""),
        "location": str(job.get("location") or job.get("location_norm") or ""),
        "salary_text": str(job.get("salary_text") or ""),
        "channel": channel,
        "chat_id": str(chat_id),
        "conversation_id": conversation_id,
    }
    return f"https://bottimviec.ai/jobs/redirect?{urlencode(params)}"


def _infer_job_source_from_url(url: str) -> str:
    try:
        host = urlsplit(url).hostname or ""
    except Exception:
        return ""
    host = host.lower()
    source_hosts = {
        "topcv.vn": "topcv",
        "vietnamworks.com": "vietnamworks",
        "careerviet.vn": "careerviet",
        "vieclam24h.vn": "vieclam24h",
        "careerlink.vn": "careerlink",
        "linkedin.com": "linkedin",
        "facebook.com": "facebook",
    }
    for domain, source in source_hosts.items():
        if host == domain or host.endswith(f".{domain}"):
            return source
    return ""


def _normalize_job_source(value: str) -> str:
    return value.strip().lower().replace(" ", "").replace("_", "").replace("-", "")


def _compact_json(data: dict, *, max_chars: int = 2000) -> str:
    try:
        text = json.dumps(data, ensure_ascii=False, default=str)
    except Exception:
        text = str(data)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."
