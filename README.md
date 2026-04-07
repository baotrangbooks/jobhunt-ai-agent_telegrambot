# Telegram & Zalo OA Integration Module

This is a comprehensive module for integrating AI Agents with Telegram and Zalo OA platforms, featuring a production-ready TelegramSender class similar to OpenClaw's implementation.

## Project Structure

```
telegram-bot/
├── models.py                    # Pydantic models (IncomingMessage)
├── telegram_integration.py      # Legacy Telegram API wrapper
├── telegram_sender.py           # Production TelegramSender class ⭐
├── telegram_sender_example.py  # Full usage examples
├── zalo_integration.py         # Zalo OA API with token management
├── webhooks.py                 # FastAPI webhook handlers
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── TELEGRAM_SENDER_README.md   # Detailed TelegramSender docs
└── README.md                   # This file
```

## Features

### Telegram (TelegramSender)
- ✅ Send text messages with markdown/HTML formatting
- ✅ Send stickers, polls, typing indicators
- ✅ Edit and delete messages
- ✅ Add reactions to messages
- ✅ Pin/unpin messages
- ✅ Forum topic support
- ✅ Inline keyboard buttons
- ✅ Reply to messages
- ✅ Thread/topic support
- ✅ Automatic text chunking (4000 char limit)
- ✅ Retry logic with exponential backoff
- ✅ Rate limiting
- ✅ Chat ID resolution (username/ID)

### Zalo OA
- ✅ Send messages
- ✅ Automatic token refresh
- ✅ Token persistence (JSON)
- ✅ Access & refresh token management

### Webhooks
- ✅ POST /webhook/telegram - Telegram message handler
- ✅ POST /webhook/zalo - Zalo message handler
- ✅ GET / - Health check

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file:
```
# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Zalo (optional)
ZALO_APP_ID=your_zalo_app_id
ZALO_APP_SECRET=your_zalo_app_secret
```

### 3. Zalo Token Initialization

For Zalo, create `tokens.json` with initial credentials:
```json
{
  "access_token": "your_access_token",
  "refresh_token": "your_refresh_token",
  "expires_in": "2024-12-31T23:59:59"
}
```

## Quick Start

### Running the Server

```bash
python main.py
```

Server starts on: `http://0.0.0.0:8008`

### Using TelegramSender

```python
from telegram_sender import TelegramSender
import asyncio

async def main():
    sender = TelegramSender()
    
    # Send a simple message
    result = await sender.send_message(
        to="YOUR_CHAT_ID",
        text="Hello, Telegram!"
    )
    print(result)  # {"ok": True, "message_id": "...", "chat_id": "..."}
    
    # Send with buttons
    buttons = [[{"text": "Click me", "callback_data": "action"}]]
    result = await sender.send_message(
        to="YOUR_CHAT_ID",
        text="Choose an option:",
        buttons=buttons
    )
    
    sender.close()

asyncio.run(main())
```

## TelegramSender Methods

| Method | Description |
|--------|-------------|
| `send_message()` | Send text message with formatting |
| `send_typing()` | Show typing indicator |
| `send_sticker()` | Send sticker |
| `send_poll()` | Send poll |
| `edit_message()` | Edit existing message |
| `delete_message()` | Delete message |
| `react_message()` | Add emoji reaction |
| `pin_message()` | Pin message |
| `create_forum_topic()` | Create forum topic |

See [TELEGRAM_SENDER_README.md](TELEGRAM_SENDER_README.md) for detailed documentation.

## Webhook Integration

### Telegram Webhook

POST `/webhook/telegram` with payload:
```json
{
  "message": {
    "message_id": 123,
    "chat": {"id": 456},
    "text": "User message"
  }
}
```

### Zalo Webhook

POST `/webhook/zalo` with payload:
```json
{
  "sender": {"id": "user_id"},
  "message": {"text": "User message"}
}
```

## Examples

### Send message with formatting

```python
# Markdown
await sender.send_message(
    to="123456789",
    text="**bold** *italic* `code`",
    text_mode="markdown"
)

# HTML
await sender.send_message(
    to="123456789",
    text="<b>bold</b> <i>italic</i> <code>code</code>",
    text_mode="html"
)
```

### Send to forum topic

```python
await sender.send_message(
    to="supergroup_id",
    text="Message in topic",
    thread_id=789  # Topic ID
)
```

### Send with retry

```python
from telegram_sender import RetryConfig

retry = RetryConfig(max_attempts=5, backoff=1.5)
await sender.send_message(
    to="123456789",
    text="With retry",
    retry=retry
)
```

### React to message

```python
await sender.react_message(
    chat_id="123456789",
    message_id=999,
    emoji="👍"
)
```

See `telegram_sender_example.py` for more examples.

## Response Format

### Success
```python
{
    "ok": True,
    "message_id": "123",
    "chat_id": "456"
}
```

### Error
```python
{
    "ok": False,
    "error": "Chat not found"
}
```

## Configuration

### Text Chunking
- Messages longer than 4000 characters are automatically split
- Respects word boundaries when possible

### Rate Limiting
- Default: 0.1s delay between API requests
- Prevents hitting Telegram rate limits

### Retry Logic
- Default: 3 attempts with exponential backoff
- Configurable via `RetryConfig` class

## Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

## Error Handling

All methods catch and log errors, returning `{"ok": False, "error": "..."}` format.

## Performance Tips

1. **Reuse session**: Keep TelegramSender instance alive for multiple calls
2. **Batch operations**: Send multiple messages efficiently
3. **Cache chat IDs**: Resolved IDs are cached for future use
4. **Use silent mode**: For non-critical messages (`silent=True`)

## Running Tests/Examples

```bash
# Run example usage
python telegram_sender_example.py

# Start webhook server
python main.py
```

## Comparison with send.ts

This implementation follows the same architecture and patterns as OpenClaw's `send.ts`:
- Async/await for all API calls
- Configurable retry logic
- Rate limiting
- Text chunking (4000 chars)
- HTML/Markdown support
- Thread parameter handling
- Inline keyboard support

## Dependencies

- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `httpx` - Async HTTP client
- `requests` - HTTP client for sync API calls
- `python-telegram-bot` - Telegram Bot API
- `python-dotenv` - Environment variables

## License

MIT
