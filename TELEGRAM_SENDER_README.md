# TelegramSender Class Documentation

Comprehensive Telegram Bot API wrapper with advanced features similar to OpenClaw's send.ts implementation.

## Features

- ✅ **Send Messages**: Text messages with markdown/HTML formatting
- ✅ **Message Editing**: Edit existing messages
- ✅ **Message Deletion**: Remove messages
- ✅ **Reactions**: Add emoji reactions to messages
- ✅ **Pins**: Pin/unpin messages
- ✅ **Typing Indicator**: Show typing status
- ✅ **Stickers**: Send sticker files
- ✅ **Polls**: Create and send polls
- ✅ **Forum Topics**: Create topics in forum-enabled supergroups
- ✅ **Inline Keyboards**: Add interactive buttons to messages
- ✅ **Threading**: Send to forum topics
- ✅ **Rate Limiting**: Built-in rate limiter
- ✅ **Retry Logic**: Configurable retry with exponential backoff
- ✅ **Chat ID Resolution**: Support for username and numeric IDs
- ✅ **Text Chunking**: Automatically split text exceeding 4000 chars
- ✅ **Silent Mode**: Send without notifications

## Installation

```bash
pip install -r requirements.txt
```

Required environment variables:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

## Quick Start

```python
from telegram_sender import TelegramSender
import asyncio

async def main():
    sender = TelegramSender()  # Uses TELEGRAM_BOT_TOKEN env var
    
    result = await sender.send_message(
        to="YOUR_CHAT_ID",  # numeric ID or @username
        text="Hello, Telegram!"
    )
    print(result)  # {"ok": True, "message_id": "...", "chat_id": "..."}
    sender.close()

asyncio.run(main())
```

## Methods

### 1. send_message()
Send a text message with optional formatting and buttons.

```python
result = await sender.send_message(
    to="123456789",          # Chat ID or username
    text="Hello!",           # Message text
    silent=False,            # No notification
    text_mode="markdown",    # markdown or html
    reply_to=None,          # Reply to message ID
    thread_id=None,         # Forum topic ID
    buttons=None,           # Inline keyboard
    retry=None              # Retry config
)
# Returns: {"ok": True, "message_id": "...", "chat_id": "..."}
```

**Options:**
- `to` (str): Chat ID (numeric) or username (@username)
- `text` (str): Message content
- `silent` (bool): Send without notification
- `text_mode` (str): "markdown" or "html"
- `reply_to` (int): Message ID to reply to
- `thread_id` (int): Forum topic ID
- `buttons` (list): Inline keyboard buttons
  ```python
  buttons = [
      [{"text": "Button 1", "callback_data": "btn1"}],
      [{"text": "Button 2", "callback_data": "btn2"}]
  ]
  ```

---

### 2. send_typing()
Show typing indicator.

```python
result = await sender.send_typing(
    to="123456789",          # Chat ID
    thread_id=None           # Forum topic ID
)
# Returns: {"ok": True}
```

---

### 3. react_message()
Add emoji reaction to a message.

```python
result = await sender.react_message(
    chat_id="123456789",     # Chat ID
    message_id=999,          # Message ID
    emoji="👍"               # Emoji reaction
)
# Returns: {"ok": True} or {"ok": False, "error": "..."}
```

---

### 4. delete_message()
Delete a message.

```python
result = await sender.delete_message(
    chat_id="123456789",     # Chat ID
    message_id=999           # Message ID
)
# Returns: {"ok": True}
```

---

### 5. edit_message()
Edit existing message text and buttons.

```python
result = await sender.edit_message(
    chat_id="123456789",     # Chat ID
    message_id=999,          # Message ID
    text="Updated text",     # New text
    text_mode="html",        # markdown or html
    buttons=None             # New buttons
)
# Returns: {"ok": True, "message_id": "...", "chat_id": "..."}
```

---

### 6. send_sticker()
Send a sticker.

```python
result = await sender.send_sticker(
    to="123456789",          # Chat ID
    file_id="CAACAgIAAxkB...",  # Sticker file ID
    silent=False,            # No notification
    reply_to=None           # Reply to message
)
# Returns: {"ok": True, "message_id": "...", "chat_id": "..."}
```

---

### 7. send_poll()
Send a poll with multiple options.

```python
poll_data = {
    "question": "What's your favorite language?",
    "options": ["Python", "JavaScript", "Go", "Rust"],
    "poll_type": "regular",  # or "quiz"
    "is_anonymous": True,
    "allows_multiple_answers": False,
    "correct_option_id": 0   # For quiz type
}

result = await sender.send_poll(
    to="123456789",
    poll_data=poll_data,
    silent=False,
    reply_to=None
)
# Returns: {"ok": True, "message_id": "...", "chat_id": "..."}
```

---

### 8. pin_message()
Pin a message in a chat.

```python
result = await sender.pin_message(
    chat_id="123456789",     # Chat ID
    message_id=999           # Message ID
)
# Returns: {"ok": True, "message_id": "...", "chat_id": "..."}
```

---

### 9. create_forum_topic()
Create a topic in a forum-enabled supergroup.

```python
result = await sender.create_forum_topic(
    chat_id="123456789",     # Forum supergroup ID
    name="General Discussion" # Topic name (max 128 chars)
)
# Returns: {"ok": True, "topic": {...}}
```

---

## Error Handling

All methods return responses in standard format:

**Success:**
```python
{
    "ok": True,
    "message_id": "123",
    "chat_id": "456"
}
```

**Error:**
```python
{
    "ok": False,
    "error": "Chat not found"
}
```

## Retry Configuration

```python
from telegram_sender import RetryConfig

retry_config = RetryConfig(
    max_attempts=3,      # Number of retries
    backoff=2.0,         # Exponential backoff multiplier
    initial_delay=0.5    # Initial delay in seconds
)

result = await sender.send_message(
    to="123456789",
    text="Message with retry",
    retry=retry_config
)
```

## Text Formatting

### Markdown Mode
```python
text = """
*italic*
**bold**
`code`
[link](https://example.com)
"""
result = await sender.send_message(to="123", text=text, text_mode="markdown")
```

### HTML Mode
```python
text = """
<i>italic</i>
<b>bold</b>
<code>code</code>
<a href="https://example.com">link</a>
"""
result = await sender.send_message(to="123", text=text, text_mode="html")
```

## Advanced Usage

### Send to Forum Topic
```python
result = await sender.send_message(
    to="123456789",
    text="Message in topic",
    thread_id=456  # Forum topic ID
)
```

### Send Reply
```python
result = await sender.send_message(
    to="123456789",
    text="This is a reply",
    reply_to=789  # Message ID to reply to
)
```

### Send Silent Message
```python
result = await sender.send_message(
    to="123456789",
    text="Silent notification",
    silent=True
)
```

### Send with Buttons
```python
buttons = [
    [
        {"text": "Yes", "callback_data": "yes_action"},
        {"text": "No", "callback_data": "no_action"}
    ]
]

result = await sender.send_message(
    to="123456789",
    text="Do you agree?",
    buttons=buttons
)
```

## Examples

See `telegram_sender_example.py` for comprehensive examples of all methods.

Run examples:
```bash
python telegram_sender_example.py
```

## Rate Limiting

The class includes built-in rate limiting:
- Default delay: 0.1 seconds between requests
- Configurable via `RateLimiter` class

## Integration with FastAPI

See `webhooks.py` for FastAPI webhook integration example.

## Comparison with send.ts

This Python implementation mirrors the functionality of OpenClaw's Telegram extension:

| Feature | send.ts | telegram_sender.py |
|---------|---------|-------------------|
| Send Message | ✅ | ✅ |
| Message Edit | ✅ | ✅ |
| Message Delete | ✅ | ✅ |
| Reactions | ✅ | ✅ |
| Pin/Unpin | ✅ | ✅ |
| Typing Indicator | ✅ | ✅ |
| Stickers | ✅ | ✅ |
| Polls | ✅ | ✅ |
| Forum Topics | ✅ | ✅ |
| Text Chunking | ✅ | ✅ |
| Inline Buttons | ✅ | ✅ |
| Retry Logic | ✅ | ✅ |
| Rate Limiting | ✅ | ✅ |
| Thread Support | ✅ | ✅ |

## License

MIT
