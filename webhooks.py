# PATCH DATETIME FIRST - before any other imports
# This fixes compatibility with Python < 3.11 for ai-agent-assistant
import patch_datetime  # type: ignore

from fastapi import FastAPI, Request
from models import IncomingMessage
from telegram_sender import TelegramSender, RetryConfig
from zalo_integration import ZaloManager
from ai_integration import get_ai_integration
from uuid import uuid4
import os
import asyncio
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "AI Chatbot Backend is running!"}

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
                    ai_integration.ensure_telegram_user(str(msg.user_id))
                    ai_integration.ensure_conversation(conversation_id, str(msg.user_id))
                    ai_integration.add_message(conversation_id, "user", msg.text_content, message_type=msg.message_type or "text")

                    history = ai_integration.load_conversation_history(conversation_id)
                    response_text, events = await ai_integration.run_turn(
                        conversation_uuid=conversation_id,
                        run_uuid=uuid4().hex[:12],
                        user_id=str(msg.user_id),
                        messages=history,
                        metadata={"user_profile": {"channel": "telegram", "telegram_chat_id": str(msg.user_id)}},
                    )

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
            ai_integration.ensure_telegram_user(f"zalo:{msg.user_id}", internal_user_id=f"zalo_{msg.user_id}")
            ai_integration.ensure_conversation(conversation_id, f"zalo:{msg.user_id}")
            ai_integration.add_message(conversation_id, "user", msg.text_content, message_type=msg.message_type or "text")

            history = ai_integration.load_conversation_history(conversation_id)
            response_text, events = await ai_integration.run_turn(
                conversation_uuid=conversation_id,
                run_uuid=uuid4().hex[:12],
                user_id=f"zalo:{msg.user_id}",
                messages=history,
                metadata={"user_profile": {"channel": "zalo", "zalo_user_id": str(msg.user_id)}},
            )
            logger.info(f"[AI Agent][Zalo] Response: {response_text[:100]}...")
            if not zalo_manager:
                logger.error("Cannot send Zalo response: ZaloManager is not initialized. Check ZALO_BOT_TOKEN.")
                return
            await zalo_manager.send_zalo_message(msg.user_id, response_text)
            logger.info(f"Message sent to Zalo: {msg.user_id}")
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


def _compact_json(data: dict, *, max_chars: int = 2000) -> str:
    try:
        text = json.dumps(data, ensure_ascii=False, default=str)
    except Exception:
        text = str(data)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."
