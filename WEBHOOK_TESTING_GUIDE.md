# 🧪 Interactive Testing Guide via Telegram Webhook

This guide explains how to test all TelegramSender examples through the Telegram webhook.

## How It Works

1. **Setup Server**: Run `python main.py`
2. **Setup Telegram Webhook**: Point your bot's webhook to your server
3. **Send Commands**: Send example names via Telegram to trigger tests
4. **Watch Results**: See the results in real-time on Telegram

## Step-by-Step Setup

### Step 1: Setup and Run Server

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your TELEGRAM_BOT_TOKEN

# Run the server
python main.py
```

Server runs on: `http://localhost:8008`

### Step 2: Setup Telegram Webhook (Local Testing)

For local testing, use ngrok to expose your server:

```bash
# Install ngrok (if not already installed)
# From: https://ngrok.com/download

# Start ngrok tunnel
ngrok http 8008
```

This gives you a public URL like: `https://abc123.ngrok.io`

### Step 3: Configure Bot Webhook

Run this command (replace placeholders):

```bash
curl -X POST \
  https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://abc123.ngrok.io/webhook/telegram"
  }'
```

Verify webhook is set:

```bash
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
```

### Step 4: Test Examples

Open Telegram and message your bot with example names:

## Available Examples

### 📝 Example 1: Simple Message
```
Send: Example 1
```
Simple text message with markdown formatting.

### 🔄 Example 2: Retry Configuration
```
Send: Example 2
```
Message sent with retry logic (max 5 attempts with exponential backoff).

### 🔘 Example 3: Inline Buttons
```
Send: Example 3
```
Message with interactive buttons (4 programming languages).
- User can click buttons
- Button data is: `lang_python`, `lang_js`, `lang_go`, `lang_rust`

### 📰 Example 4: HTML Formatting
```
Send: Example 4
```
Message with HTML formatting:
- **Bold text**
- *Italic text*
- `Code blocks`
- [Links](https://example.com)

### ⌨️ Example 5: Typing Indicator
```
Send: Example 5
```
Shows "typing..." for 2 seconds, then sends "I was typing... done! 👍"

### 🗳️ Example 6: Poll
```
Send: Example 6
```
Creates a poll asking "What's your favorite Python version?"
Options: 3.8, 3.9, 3.10, 3.11, 3.12

### ✏️ Example 7: Edit Message
```
Send: Example 7
```
Sends "Original message (will be edited)"
Waits 1 second, then edits to "Edited message with updated content! ✏️"

### 📌 Example 8: Pin Message
```
Send: Example 8
```
Sends "This message will be pinned! 📌"
Then pins the message in the chat.

### 👍 Example 9: React to Message
```
Send: Example 9
```
Sends "React to this message with 👍"
Then adds 👍 reaction to the message.

### 🔕 Example 10: Buttons with Silent Mode
```
Send: Example 10
```
Sends "Do you like these examples?" with Yes/No buttons
Message sends silently (no notification sound).

### 📚 Help
```
Send: help
```
Shows all available examples and commands.

## Testing Workflow

### Complete Test Sequence

```
1. Send "help" → See all available commands
2. Send "Example 1" → Simple message test
3. Send "Example 2" → Retry test
4. Send "Example 3" → Click the buttons and see callback data
5. Send "Example 4" → Verify HTML formatting
6. Send "Example 5" → Watch typing indicator
7. Send "Example 6" → Vote in the poll
8. Send "Example 7" → Watch message being edited
9. Send "Example 8" → Check pinned message
10. Send "Example 9" → Verify reaction added
11. Send "Example 10" → Send silently (no notification)
```

## Advanced Testing

### Test Multiple Chats
Send examples to different chats/groups to verify bot works in different contexts.

### Test Callback Handling
For Example 3, when users click buttons:
- Currently buttons just show callback_data
- You can extend to handle callbacks in `/webhook/telegram`

### Monitor Logs
Watch the console output:

```
INFO:__main__:Processing message from tele: Example 1
INFO:__main__:Running example: example 1
INFO:__main__:Running Example 1: Simple text message
INFO:__main__:Example example 1 executed successfully: {'ok': True, 'message_id': '123', 'chat_id': '456'}
```

## Troubleshooting

### "Telegram webhook not working"

**Check 1: Webhook is set**
```bash
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
# Should show your URL
```

**Check 2: Firewall/Port**
- Make sure port 8008 is accessible
- With ngrok, it's automatically forwarded

**Check 3: Server is running**
```bash
# Test locally
curl http://localhost:8008/
# Should return: {"message": "AI Chatbot Backend is running!"}
```

### "Example command not recognized"

- Check capitalization: "Example 1" (capital E)
- Check spelling: "Example" (not "example", "Example1", etc.)
- Send "help" to see exact format

### "Button clicks not working"

Currently the webhook just receives the click data. To handle it:

1. Update webhook to parse callback_query:
```python
@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()
    if "callback_query" in data:
        # Handle button click
        callback_data = data["callback_query"]["data"]
        # ... your handler code
    elif "message" in data:
        # Handle text message
        # ... existing code
```

### "Rate limit errors"

- Wait a few moments before sending more commands
- TelegramSender has built-in rate limiting

## Production Deployment

### Using Public Domain

Replace ngrok URL with your actual domain:

```bash
curl -X POST \
  https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://yourdomain.com/webhook/telegram"
  }'
```

### Using Environment Variables

Store in .env:
```
TELEGRAM_BOT_TOKEN=your_token
WEBHOOK_URL=https://yourdomain.com
```

Then in code:
```python
webhook_url = os.getenv("WEBHOOK_URL")
```

### Run Behind Reverse Proxy

Use nginx, Apache, or similar to forward requests to your app running locally.

## Extending Examples

### Add Your Own Example

1. Create a function in `webhooks.py`:

```python
async def example_11(sender: TelegramSender, chat_id: str):
    """Example 11: Your custom action"""
    logger.info("Running Example 11: Your custom action")
    result = await sender.send_message(
        to=chat_id,
        text="Example 11: Your custom message"
    )
    return result
```

2. Add to EXAMPLES dict:

```python
EXAMPLES = {
    # ... existing examples ...
    "example 11": example_11,
}
```

3. Test: Send "Example 11" in Telegram

## Quick Command Reference

| Command | Action |
|---------|--------|
| `help` | Show all examples |
| `Example 1` | Simple message |
| `Example 2` | Retry config |
| `Example 3` | Buttons |
| `Example 4` | HTML formatting |
| `Example 5` | Typing indicator |
| `Example 6` | Poll |
| `Example 7` | Edit message |
| `Example 8` | Pin message |
| `Example 9` | React emoji |
| `Example 10` | Silent + buttons |

## Testing Checklist

- [ ] Server running (`python main.py`)
- [ ] .env configured with bot token
- [ ] Webhook URL set correctly
- [ ] Can send messages to bot
- [ ] "help" command works
- [ ] Example 1 sends simple message
- [ ] Example 3 buttons are clickable
- [ ] Example 5 shows typing indicator
- [ ] Example 6 creates a working poll
- [ ] Example 8 pins message
- [ ] Logs show processing messages

## Debugging Tips

1. **Enable verbose logging**:
```python
logging.basicConfig(level=logging.DEBUG)
```

2. **Print incoming data**:
```python
@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()
    print(json.dumps(data, indent=2))  # Debug log
    # ... rest of code
```

3. **Test locally first**:
```python
# test_local.py
import asyncio
from telegram_sender import TelegramSender

async def test():
    sender = TelegramSender()
    result = await sender.send_message(
        to="YOUR_CHAT_ID",
        text="Test message"
    )
    print(result)
    sender.close()

asyncio.run(test())
```

## Performance Testing

### Stress Test Examples

```
Send these rapidly:
Example 1
Example 2
Example 3
Example 4
Example 5
```

Watch how the bot handles rapid requests.

### Response Time Monitoring

Check logs for timing:
```
2026-04-07 10:30:45 - Processing message
2026-04-07 10:30:46 - Response sent (1s response time)
```

## Next Steps

1. ✅ Test all 10 examples
2. 🔄 Add your own custom examples
3. 🤖 Integrate real AI processing
4. 📊 Monitor and log results
5. 🚀 Deploy to production

---

**Have fun testing!** 🎉

For support, see:
- TELEGRAM_SENDER_README.md - API documentation
- telegram_sender_example.py - Code examples
- README.md - Project overview
