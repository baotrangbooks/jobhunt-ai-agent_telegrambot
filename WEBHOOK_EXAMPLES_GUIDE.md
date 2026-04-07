# 🎯 Complete Webhook Testing Guide

## Overview

The webhook system now supports **10 interactive examples** that you can test by sending simple text messages to your Telegram bot.

## Architecture

```
User sends message to bot
    ↓
Telegram forwards to webhook (/webhook/telegram)
    ↓
Webhook parses message → IncomingMessage
    ↓
process_with_ai() checks if message is an example command
    ↓
If command found, runs corresponding example handler
    ↓
Handler executes TelegramSender method
    ↓
Result sent back to user via Telegram
```

## Quick Start (3 minutes)

### 1. Prepare Environment
```bash
# Copy template if needed
cp .env.example .env

# Edit .env and set your bot token
# TELEGRAM_BOT_TOKEN=your_actual_token_here
```

### 2. Start Server
```bash
python main.py
```

### 3. Test Locally First (Optional)
```bash
# In a new terminal
python test_webhook_local.py
```

This tests all examples WITHOUT needing Telegram or webhook setup.

### 4. Setup Real Telegram Testing

#### Option A: Using ngrok (Easiest for Local)
```bash
# Terminal 1: Start server
python main.py

# Terminal 2: Start ngrok tunnel
ngrok http 8008

# Terminal 3: Set webhook (replace URL and TOKEN)
curl -X POST \
  https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://your_ngrok_url/webhook/telegram"}'

# Now message your bot on Telegram!
```

#### Option B: Production Domain
```bash
# Replace ngrok URL with your real domain
curl -X POST \
  https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://yourdomain.com/webhook/telegram"}'
```

### 5. Test in Telegram

Send these messages to your bot:

1. Send: `help` → See all available commands
2. Send: `Example 1` → Test simple message
3. Send: `Example 2` → Test retry config
4. ... and so on through Example 10

## Example Commands & Results

### Command: `help`
**Response**: Shows all 10 available examples with brief descriptions

### Command: `Example 1`
**Response**: Simple markdown text message
```
"Hello! This is Example 1 - a simple test message."
```

### Command: `Example 2`
**Response**: Same message but sent with retry configuration (max 5 attempts)
```
"This is Example 2 - Message with retry configuration"
```

### Command: `Example 3`
**Response**: Message with 4 interactive buttons (2x2 grid)
```
Text: "Choose your favorite programming language:"
Buttons:
  [Python]  [JavaScript]
  [Go]      [Rust]
```
Users can click buttons and see callback_data.

### Command: `Example 4`
**Response**: HTML formatted message
```
Bold text
Italic text
code
Link to example
```

### Command: `Example 5`
**Response**: 
1. Shows typing indicator for 2 seconds
2. Then sends message: "I was typing... done! 👍"

### Command: `Example 6`
**Response**: Creates a poll
```
Question: "What's your favorite Python version?"
Options: [3.8] [3.9] [3.10] [3.11] [3.12]
```
Users can vote in the poll.

### Command: `Example 7`
**Response**: Sends message, then edits it
1. First: "Original message (will be edited)"
2. After 1 sec: "Edited message with updated content! ✏️"

### Command: `Example 8`
**Response**: Sends message, then pins it
1. Sends: "This message will be pinned! 📌"
2. Then: Message appears as pinned in chat

### Command: `Example 9`
**Response**: Sends message, then adds emoji reaction
1. Sends: "React to this message with 👍"
2. Then: Adds 👍 reaction to the message

### Command: `Example 10`
**Response**: Message with buttons + silent mode (no notification sound)
```
Text: "Do you like these examples?"
Buttons:
  [✅ Yes]  [❌ No]
Send silently (no notification sound)
```

## Message Flow Example

**User sends**: `Example 1`

**Webhook receives**:
```json
{
  "message": {
    "message_id": 123,
    "chat": {"id": 456789},
    "text": "Example 1"
  }
}
```

**Process flow**:
1. ✅ Parse message → `IncomingMessage(user_id="456789", text_content="Example 1", platform="tele")`
2. ✅ Call `process_with_ai(msg)`
3. ✅ Check command: "example 1" (lowercased) → matches in EXAMPLES dict
4. ✅ Call `example_1(sender, "456789")`
5. ✅ `example_1()` calls `sender.send_message(to="456789", text="Hello! This is Example 1...")`
6. ✅ Message sent to Telegram
7. ✅ User sees message in Telegram chat

**Console logs**:
```
INFO:__main__:Processing message from tele: Example 1
INFO:__main__:Running example: example 1
INFO:__main__:Running Example 1: Simple text message
INFO:__main__:Example example 1 executed successfully: {'ok': True, 'message_id': '789', 'chat_id': '456789'}
```

## File Structure

```
webhooks.py:
├── example_1() - Simple message
├── example_2() - Retry config
├── example_3() - Buttons
├── example_4() - HTML
├── example_5() - Typing indicator
├── example_6() - Poll
├── example_7() - Edit message
├── example_8() - Pin message
├── example_9() - React message
├── example_10() - Silent + buttons
├── example_help() - Show help
├── EXAMPLES dict - Command map
└── process_with_ai() - Main handler
```

## How It Works

### 1. Command Recognition

```python
EXAMPLES = {
    "example 1": example_1,
    "example 2": example_2,
    # ... etc ...
    "help": example_help,
}
```

When message arrives:
- Lowercased: `"Example 1".lower()` → `"example 1"`
- Looked up in EXAMPLES dict
- If found → calls handler function
- If not found → returns default AI response

### 2. Handler Execution

Each example handler:
```python
async def example_N(sender: TelegramSender, chat_id: str):
    logger.info(f"Running Example N: ...")
    result = await sender.send_message(...)
    return result
```

Receives:
- `sender`: TelegramSender instance
- `chat_id`: Where to send the message

Returns:
- `{ok: True, message_id: "...", chat_id: "..."}`
- or `{ok: False, error: "..."}`

### 3. Result Handling

```python
if result.get("ok"):
    logger.info(f"Example executed successfully: {result}")
else:
    logger.error(f"Example failed: {result.get('error')}")
```

## Testing Scenarios

### Scenario 1: Full Feature Test
```
1. Send: help                 → Verify help works
2. Send: Example 1            → Verify message sent
3. Send: Example 3            → Click buttons
4. Send: Example 5            → Watch typing
5. Send: Example 6            → Vote in poll
6. Send: Example 8            → Check pinned
7. Send: Example 9            → Check reaction
```

### Scenario 2: Error Handling
```
1. Send: "invalid command"    → Should get AI response
2. Send: "Example 999"        → Should get AI response
3. Send: ""                   → Should handle gracefully
4. Send: "EXAMPLE 1"          → Should work (case insensitive)
```

### Scenario 3: Stress Test
```
Rapidly send:
- Example 1
- Example 2
- Example 3
- Example 4
- Example 5

Watch how bot handles concurrent requests
```

## Troubleshooting

### Problem: Messages not arriving at webhook

**Check 1**: Webhook is registered
```bash
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
```
Should show your webhook URL.

**Check 2**: Server is running
```bash
curl http://localhost:8008/
```
Should return: `{"message": "AI Chatbot Backend is running!"}`

**Check 3**: ngrok is still running
```bash
# If using ngrok, check the terminal it's running in
# Should show: "Session Status  online"
```

### Problem: Example commands not recognized

**Check**: Exact spelling
- ✅ Correct: `Example 1` (capital E)
- ❌ Wrong: `example 1` (lowercase start)
- ❌ Wrong: `Example1` (no space)

Send `help` to see exact format.

### Problem: "TELEGRAM_BOT_TOKEN not provided"

**Fix**: 
1. Edit or create `.env`
2. Add: `TELEGRAM_BOT_TOKEN=your_actual_token`
3. Restart `python main.py`

### Problem: Buttons not responding

**Current behavior**: Buttons show callback_data when clicked
**Future enhancement**: Can add callback handler to execute actions

## Customization

### Add Your Own Example

1. Create handler function:
```python
async def example_11(sender: TelegramSender, chat_id: str):
    """Example 11: Your custom feature"""
    result = await sender.send_message(
        to=chat_id,
        text="Your message here"
    )
    return result
```

2. Add to EXAMPLES dict:
```python
EXAMPLES = {
    # ... existing ...
    "example 11": example_11,
}
```

3. Test: Send `Example 11` in Telegram

### Modify Default Response

Change this function to customize non-example messages:
```python
async def process_with_ai(msg: IncomingMessage):
    # ... example handling ...
    else:
        # Change this response
        response_text = f"Custom response: {msg.text_content}"
        # ...
```

## Monitoring & Debugging

### View Real-Time Logs

Terminal shows:
```
INFO:__main__:Processing message from tele: Example 1
INFO:__main__:Running example: example 1
INFO:__main__:Running Example 1: Simple text message
INFO:__main__:Example example 1 executed successfully: {'ok': True, ...}
```

### Debug Message Payload

Add to webhook:
```python
@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()
    print(json.dumps(data, indent=2))  # Debug
    # ... rest of code
```

### Check Response

After sending message in Telegram:
- ✅ Message appears in chat
- ✅ Console shows success log
- ✅ `{'ok': True, ...}` in logs

## Performance Tips

1. **Reuse sender**: Keep TelegramSender instance alive
   - Current: Creates new for each message ✅
   - Could optimize: Cache sender instance

2. **Rate limiting**: Built-in 0.1s delay works well
   - Won't hit Telegram's rate limits
   - Safe to send rapid examples

3. **Logging**: Uses asyncio for non-blocking I/O
   - Doesn't slow down requests
   - Can handle concurrent messages

## Testing With Tools

### Using curl
```bash
# Simulate webhook request
curl -X POST http://localhost:8008/webhook/telegram \
  -H 'Content-Type: application/json' \
  -d '{
    "message": {
      "message_id": 123,
      "chat": {"id": 456789},
      "text": "Example 1"
    }
  }'
```

### Using Postman
1. Create POST request to `http://localhost:8008/webhook/telegram`
2. Set header: `Content-Type: application/json`
3. Add body:
```json
{
  "message": {
    "message_id": 123,
    "chat": {"id": 456789},
    "text": "Example 1"
  }
}
```
4. Send and observe response

### Using Python
```python
import requests

response = requests.post(
    "http://localhost:8008/webhook/telegram",
    json={
        "message": {
            "message_id": 123,
            "chat": {"id": 456789},
            "text": "Example 1"
        }
    }
)
print(response.json())
```

## Next Steps

1. ✅ Test all 10 examples in Telegram
2. 🔄 Try the stress test scenario
3. 📝 Add your own custom examples
4. 🤖 Integrate real AI processing
5. 🚀 Deploy to production
6. 📊 Monitor and optimize

## Related Documentation

- [WEBHOOK_TESTING_GUIDE.md](WEBHOOK_TESTING_GUIDE.md) - Extended guide
- [TELEGRAM_SENDER_README.md](TELEGRAM_SENDER_README.md) - API reference
- [GETTING_STARTED.md](GETTING_STARTED.md) - Setup guide
- [README.md](README.md) - Project overview

---

**Ready to test?** 🎉

```bash
python main.py                    # Start server
# then in Telegram: send "Example 1"
```
