# 🚀 QUICK START - Webhook Testing

## What's New?

The webhook now supports **10 interactive examples** you can test by sending text messages to your Telegram bot!

```
You: "Example 1"           Bot: Sends simple message
You: "Example 2"           Bot: Sends with retry config
You: "Example 3"           Bot: Sends message with buttons 🔘
You: "Example 4"           Bot: Sends HTML formatted text
You: "Example 5"           Bot: Shows typing indicator ⌨️
You: "Example 6"           Bot: Creates a poll 🗳️
You: "Example 7"           Bot: Edits a message ✏️
You: "Example 8"           Bot: Pins a message 📌
You: "Example 9"           Bot: Adds emoji reaction 👍
You: "Example 10"          Bot: Sends with silent mode 🔕
```

## 5-Minute Setup

### Step 1: Get Bot Token
1. Open Telegram → search `@BotFather`
2. Send `/newbot`
3. Follow prompts
4. Copy your token (format: `123456789:ABCdef...`)

### Step 2: Setup Environment
```bash
# In project folder
cp .env.example .env
# Edit .env and paste your token:
# TELEGRAM_BOT_TOKEN=123456789:ABCdef...
```

### Step 3: Run Server
```bash
python main.py
```
✅ Server running on `http://localhost:8008`

### Step 4: Expose Local Server
```bash
# New terminal - Install/run ngrok
ngrok http 8008
```
✅ You'll get URL like: `https://abc123.ngrok.io`

### Step 5: Set Telegram Webhook
```bash
# Replace TOKEN and ngrok_URL
curl -X POST \
  https://api.telegram.org/bot<TOKEN>/setWebhook \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://abc123.ngrok.io/webhook/telegram"}'
```

### Step 6: Test in Telegram
1. Open Telegram
2. Message your bot: `help`
3. You'll see all available examples
4. Try: `Example 1`
5. See response in chat! 🎉

## Full Test Sequence

```
Send to bot:        Expected response:
─────────────────────────────────────────────────
"help"              → Shows all commands
"Example 1"         → Simple text message
"Example 2"         → Message with retry
"Example 3"         → Message with buttons
"Example 4"         → HTML formatted text
"Example 5"         → Typing indicator
"Example 6"         → Poll (vote on it!)
"Example 7"         → Edits the message
"Example 8"         → Pins the message
"Example 9"         → Adds emoji reaction
"Example 10"        → Silent message + buttons
```

## Test Locally First (No Telegram)

```bash
# Skip if you want to test on real Telegram
python test_webhook_local.py
```

This runs all 10 examples locally to verify they work.

## Architecture

```
📱 Telegram
    ↓
🔗 Webhook receives message
    ↓
📝 Parse command (e.g., "Example 1")
    ↓
🔍 Lookup in examples dictionary
    ↓
⚙️ Execute matching handler
    ↓
📤 Send result back to Telegram
    ↓
✅ User sees result in chat
```

## File Locations

| File | Purpose |
|------|---------|
| `webhooks.py` | Example handlers (all 10 examples) |
| `telegram_sender.py` | Core TelegramSender class |
| `main.py` | FastAPI server |
| `.env` | Your bot token (keep secret!) |
| `WEBHOOK_EXAMPLES_GUIDE.md` | Complete webhook guide |
| `WEBHOOK_TESTING_GUIDE.md` | Extended testing guide |

## The Examples

### Example 1: Simple Message
```python
await sender.send_message(
    to=chat_id,
    text="Hello! This is Example 1 - a simple test message.",
    text_mode="markdown"
)
```

### Example 2: With Retry
```python
retry_config = RetryConfig(max_attempts=5, backoff=1.5)
await sender.send_message(
    to=chat_id,
    text="Message with retry configuration",
    retry=retry_config
)
```

### Example 3: With Buttons
```python
buttons = [[
    {"text": "Python", "callback_data": "lang_python"},
    {"text": "JavaScript", "callback_data": "lang_js"}
]]
await sender.send_message(
    to=chat_id,
    text="Choose language:",
    buttons=buttons
)
```

### Example 4: HTML Format
```python
await sender.send_message(
    to=chat_id,
    text="<b>Bold</b> <i>Italic</i> <code>Code</code>",
    text_mode="html"
)
```

### Example 5: Typing Indicator
```python
await sender.send_typing(to=chat_id)
await asyncio.sleep(2)
await sender.send_message(to=chat_id, text="Done!")
```

### Example 6: Poll
```python
await sender.send_poll(
    to=chat_id,
    poll_data={
        "question": "Best Python version?",
        "options": ["3.10", "3.11", "3.12"]
    }
)
```

### Example 7: Edit Message
```python
send_result = await sender.send_message(to=chat_id, text="Original")
await sender.edit_message(
    chat_id=chat_id,
    message_id=send_result["message_id"],
    text="Edited version!"
)
```

### Example 8: Pin Message
```python
send_result = await sender.send_message(to=chat_id, text="Pin me!")
await sender.pin_message(chat_id, send_result["message_id"])
```

### Example 9: React With Emoji
```python
send_result = await sender.send_message(to=chat_id, text="React to me")
await sender.react_message(chat_id, send_result["message_id"], emoji="👍")
```

### Example 10: Silent + Buttons
```python
buttons = [[{"text": "Yes", "callback_data": "yes"}]]
await sender.send_message(
    to=chat_id,
    text="Silent question?",
    buttons=buttons,
    silent=True
)
```

## How It Works in Code

In `webhooks.py`:

```python
# When message arrives
async def process_with_ai(msg: IncomingMessage):
    command = msg.text_content.strip().lower()  # "example 1"
    
    if command in EXAMPLES:
        # Found matching example
        handler = EXAMPLES[command]  # Get example_1 function
        result = await handler(sender, msg.user_id)  # Execute
        return result
    else:
        # Default AI response
        return await sender.send_message(msg.user_id, f"AI: {msg.text_content}")
```

EXAMPLES dictionary:
```python
EXAMPLES = {
    "example 1": example_1,
    "example 2": example_2,
    # ... etc ...
    "help": example_help,
}
```

Each handler:
```python
async def example_1(sender: TelegramSender, chat_id: str):
    result = await sender.send_message(
        to=chat_id,
        text="Hello! This is Example 1..."
    )
    return result
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Chat not found" | Check your chat ID is correct |
| Webhook not working | Verify webhook URL is set with `getWebhookInfo` |
| No bot token | Edit `.env` with your actual token |
| Command not recognized | Use exact spelling: `Example 1` (capital E) |
| ngrok keeps closing | Keep terminal open, make new one for bot |

## Performance

- ✅ Handles concurrent messages smoothly
- ✅ Built-in rate limiting (0.1s between requests)
- ✅ Automatic retry with exponential backoff
- ✅ Non-blocking asyncio operations
- ✅ Production-ready

## Feature Checklist

- [x] Send simple messages
- [x] Format with markdown/HTML
- [x] Add inline buttons
- [x] Edit messages
- [x] Delete messages
- [x] Add reactions
- [x] Create polls
- [x] Show typing indicator
- [x] Pin messages
- [x] Silent mode
- [x] Thread/forum support
- [x] Retry logic
- [x] Rate limiting
- [x] Webhook integration

## Next Steps

1. ✅ Follow 5-minute setup above
2. 🤖 Test all 10 examples in Telegram
3. 📝 Add your own custom examples (edit `webhooks.py`)
4. 🔗 Integrate with real AI agent
5. 🚀 Deploy to production

## Documentation Files

* [WEBHOOK_EXAMPLES_GUIDE.md](WEBHOOK_EXAMPLES_GUIDE.md) - **This file** (quick overview)
* [WEBHOOK_TESTING_GUIDE.md](WEBHOOK_TESTING_GUIDE.md) - Detailed testing guide
* [TELEGRAM_SENDER_README.md](TELEGRAM_SENDER_README.md) - API reference
* [README.md](README.md) - Project overview
* [GETTING_STARTED.md](GETTING_STARTED.md) - Initial setup guide

## Setup Helper

Run the interactive setup helper:
```bash
python setup_webhook_testing.py
```

This checks dependencies, shows instructions, and troubleshooting tips.

## Need Help?

1. Check console logs: `python main.py` shows debug info
2. Test locally first: `python test_webhook_local.py`
3. Use curl to test webhook: See WEBHOOK_TESTING_GUIDE.md
4. Read: WEBHOOK_EXAMPLES_GUIDE.md for detailed info

---

## 30-Second Summary

```bash
# 1. Setup
cp .env.example .env
# Edit: add your TELEGRAM_BOT_TOKEN

# 2. Run server
python main.py

# 3. Expose (new terminal)
ngrok http 8008

# 4. Set webhook (one command)
curl -X POST https://api.telegram.org/bot<TOKEN>/setWebhook \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://ngrok_url/webhook/telegram"}'

# 5. Test in Telegram
Send: "Example 1" → See message appear! 🎉
```

**That's it! You're ready to go.** 🚀
