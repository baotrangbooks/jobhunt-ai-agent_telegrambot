# 🚀 Getting Started with TelegramSender

Quick guide to get up and running with the TelegramSender implementation.

## 1️⃣ Installation (5 minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Get a Telegram Bot Token
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the prompts to create your bot
4. Copy your bot token (format: `123456789:ABCdefGhIjKLmnoPqrStUvWxYz`)

### Step 3: Setup Environment
```bash
# Copy example to .env
cp .env.example .env

# Edit .env and add your bot token
# TELEGRAM_BOT_TOKEN=your_token_here
```

## 2️⃣ First Message (2 minutes)

Create `test_send.py`:
```python
from telegram_sender import TelegramSender
import asyncio

async def main():
    sender = TelegramSender()
    
    # Get your chat ID first (DM the bot or check your user ID)
    chat_id = "123456789"  # Replace with your chat ID
    
    result = await sender.send_message(
        to=chat_id,
        text="Hello from TelegramSender! 🎉"
    )
    
    print(result)
    sender.close()

asyncio.run(main())
```

Run:
```bash
python test_send.py
```

Expected output:
```
{'ok': True, 'message_id': '123', 'chat_id': '456789'}
```

## 3️⃣ Get Your Chat ID

### Method 1: Send yourself a message
```python
# Get test message from bot
# Then check the Telegram API response for chat_id
```

### Method 2: Use an existing bot
- Send a message to your bot
- Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
- Look for `"chat"` → `"id"`

## 4️⃣ Common Tasks

### Send Message with Formatting
```python
await sender.send_message(
    to="123456789",
    text="**Bold** *italic* `code`",
    text_mode="markdown"
)
```

### Send with Buttons
```python
buttons = [[
    {"text": "Yes ✓", "callback_data": "yes"},
    {"text": "No ✗", "callback_data": "no"}
]]

await sender.send_message(
    to="123456789",
    text="Do you like TelegramSender?",
    buttons=buttons
)
```

### React to a Message
```python
await sender.react_message(
    chat_id="123456789",
    message_id=999,
    emoji="👍"
)
```

### Send a Poll
```python
poll_data = {
    "question": "Best Python Version?",
    "options": ["3.10", "3.11", "3.12"],
    "poll_type": "regular"
}

await sender.send_poll(
    to="123456789",
    poll_data=poll_data
)
```

## 5️⃣ Run All Examples

```bash
python telegram_sender_example.py
```

This runs 15 different examples showing all features.

## 6️⃣ Start the Webhook Server

```bash
python main.py
```

Server runs on `http://0.0.0.0:8008`

Visit `http://localhost:8008/` to check if it's running.

### Setup Telegram Webhook

```bash
curl -X POST \
  https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://yourdomain.com/webhook/telegram"
  }'
```

## 7️⃣ Troubleshooting

### "TELEGRAM_BOT_TOKEN not provided"
- Check `.env` file exists
- Make sure `TELEGRAM_BOT_TOKEN=...` is set
- Verify token format (should end with long string after `:`)

### "Chat not found"
- Make sure you're using the correct chat ID
- Bot must be a member of the chat/group
- For groups, use the numeric ID (starts with `-`)

### Messages not sending
- Check bot token is correct
- Verify chat ID exists
- Check internet connection
- Look at error message

### Rate limit errors
- Wait a few seconds before retrying
- Built-in rate limiter helps prevent this
- Telegram allows ~30 msg/sec per bot

## 8️⃣ Testing

Run the test suite:
```bash
pytest test_telegram_sender.py -v
```

## 9️⃣ Next Steps

1. **Read Full Docs**: See [TELEGRAM_SENDER_README.md](TELEGRAM_SENDER_README.md)
2. **Explore Examples**: Check [telegram_sender_example.py](telegram_sender_example.py)
3. **Build Integration**: Modify [webhooks.py](webhooks.py) for your use case
4. **Deploy**: Run on production server

## 🔟 Quick Reference

### Basic Template
```python
from telegram_sender import TelegramSender, RetryConfig
import asyncio

async def main():
    sender = TelegramSender()
    
    try:
        result = await sender.send_message(
            to="YOUR_CHAT_ID",
            text="Your message here",
            # Options:
            # silent=True,
            # text_mode="html",
            # buttons=[[{"text": "Btn", "callback_data": "action"}]],
            # reply_to=999,
            # thread_id=123,
        )
        print("✓ Success:", result)
    except Exception as e:
        print("✗ Error:", e)
    finally:
        sender.close()

asyncio.run(main())
```

## 📚 Resources

- [Telegram Bot API Docs](https://core.telegram.org/bots/api)
- [Full Documentation](TELEGRAM_SENDER_README.md)
- [Examples](telegram_sender_example.py)
- [Tests](test_telegram_sender.py)

## 💡 Tips

1. **Keep bot token secret** - Store in `.env`, never commit
2. **Use async/await** - All methods are async
3. **Cache chat IDs** - Resolved IDs are cached automatically
4. **Handle errors** - Check `result['ok']` before using message_id
5. **Test locally first** - Run examples before production

## 🎯 Common Use Cases

### AI Chatbot
```python
async def handle_message(user_message):
    # Process with AI
    ai_response = await ai_agent.process(user_message)
    # Send response
    await sender.send_message(to=chat_id, text=ai_response)
```

### Status Notification
```python
await sender.send_message(
    to=admin_chat_id,
    text=f"🔔 Status: {status}",
    silent=True  # No notification noise
)
```

### Interactive Poll
```python
await sender.send_poll(
    to=chat_id,
    poll_data={
        "question": "Vote on feature",
        "options": ["Option A", "Option B"],
        "poll_type": "quiz"
    }
)
```

---

**Ready to go?** Start with example #1 above! 🚀
