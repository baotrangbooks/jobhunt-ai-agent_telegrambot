# 🤖 Telegram Bot + AI Agent Integration

**Telegram bot tích hợp với AI Chatbot Agent để trò chuyện thông minh**

## ⚡ Quick Start (5 phút)

### 1. Cài đặt Environment (lần đầu)

```bash
# Setup venv
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Cấu hình (copy .env.example → .env)

```bash
copy .env.example .env
# Edit .env and add your tokens:
# - TELEGRAM_BOT_TOKEN (từ @BotFather)
# - OPENAI_API_KEY
```

### 3. Chạy Server

```bash
# Activate venv
.\.venv\Scripts\activate

# Start server
python run.py
```

### 4. Setup Webhook (trên server công khai)

```bash
# Option A: Setup sẵn có domain
python telegram_webhook_setup.py

# Option B: Manual
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://your-domain.com:8000/webhook/telegram"
```

### 5. Test

```bash
# Test integration
python test_ai_integration.py
```

## 📁 File Structure

```
telegram-bot/
├── ai_integration.py              # AI agent integration layer
├── webhooks.py                    # FastAPI webhook handlers (SỬA)
├── telegram_sender.py             # Telegram API client
├── models.py                      # Data models
├── run.py                         # Start server
├── telegram_webhook_setup.py      # Setup webhook tool
├── test_ai_integration.py         # Test script
├── AI_AGENT_INTEGRATION_GUIDE.md  # Full documentation
├── .env.example                   # Environment template
└── requirements.txt               # Dependencies
```

## 🔄 Integration Flow

```
User Message (Telegram)
    ↓
/webhook/telegram (FastAPI)
    ↓
process_with_ai()
    ├──→ Check if "help" or "example X"
    ├──→ If yes: run example
    └──→ If no: call AI agent
    ↓
ai_integration.get_response()
    ├──→ Load conversation history
    ├──→ Call OpenAI + LangGraph agent
    ├──→ Store in memory
    └──→ Return response
    ↓
telegram_sender.send_message()
    └──→ Send to user
```

## 📊 Key Features

- ✅ **Real AI Conversations** - Dùng OpenAI + LangGraph
- ✅ **Conversation Memory** - SQLite persistence per user
- ✅ **Async Processing** - FastAPI webhook
- ✅ **Message Chunking** - Auto-split > 4096 chars
- ✅ **Retry Logic** - Exponential backoff
- ✅ **Rate Limiting** - Token bucket algorithm
- ✅ **Example Commands** - 14 examples included
- ✅ **Multiple Platforms** - Telegram + Zalo support

## 🔧 Configuration

### Minimal (.env)

```env
TELEGRAM_BOT_TOKEN=...
OPENAI_API_KEY=...
```

### Full (.env)

```env
TELEGRAM_BOT_TOKEN=...
OPENAI_API_KEY=...
WEBHOOK_URL=https://your-domain.com:8000/webhook/telegram
AI_MEMORY_DB=ai_memory.db
LOG_LEVEL=INFO
```

## 📝 Main Changes to Original

### webhooks.py (Modified)

- Added `from ai_integration import get_ai_integration`
- Modified `process_with_ai()` function:
  - Instead of hardcoded response
  - Calls `get_ai_response()` from AI agent
  - Auto-splits long messages
  - Handles streaming responses

### New Files

1. **ai_integration.py** (350 lines)
   - AIAgentIntegration class
   - Conversation memory management
   - LangChain integration
   - Async streaming support

2. **run.py** (100 lines)
   - Server startup script
   - Configuration validation
   - Logging setup

3. **telegram_webhook_setup.py** (250 lines)
   - Interactive webhook setup
   - Bot validation
   - Status checking

4. **test_ai_integration.py** (350 lines)
   - 6 integration tests
   - Environment check
   - AI chat test

5. **AI_AGENT_INTEGRATION_GUIDE.md**
   - Complete setup guide
   - Troubleshooting
   - Architecture explanation

## 🚀 Usage Examples

### Simple Chat

```bash
# Open Telegram and message your bot
User: "Hello"
Bot: "Hello! How can I assist you today?"

User: "What is AI?"
Bot: "AI (Artificial Intelligence) is..."
```

### With Examples

```bash
User: "help"
Bot: [Shows 14 example commands]

User: "example 3"
Bot: [Sends message with buttons]
```

### Conversation Context

```bash
User: "My name is John"
Bot: "Nice to meet you, John!"

User: "What's my name?"
Bot: "Your name is John" (from memory)
```

## 🧪 Testing

### Import Test

```bash
python -c "from ai_integration import get_ai_integration; print('OK')"
```

### Full Integration Test

```bash
python test_ai_integration.py
```

Expected output:
```
✅ All tests passed! System is ready to use.
```

### Manual Test

```bash
# Terminal 1: Start server
python run.py

# Terminal 2: Send test
curl -X POST http://localhost:8000/webhook/telegram \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "text": "Hello",
      "chat": {"id": "123"},
      "from": {"id": "123"}
    }
  }'
```

## 🔍 Monitoring

### View Logs

```bash
# Server logs (real-time)
tail -f debug.log

# Check conversation
python -c "
import asyncio
from ai_integration import get_ai_integration
ai = asyncio.run(get_ai_integration())
stats = ai.get_conversation_stats(user_id=123)
print(stats)
"
```

### Database

```bash
# View SQLite database
sqlite3 ai_memory.db

# Query conversations
SELECT * FROM conversations;
```

## ⚠️ Common Issues

### "TELEGRAM_BOT_TOKEN not found"
→ Add to .env: `TELEGRAM_BOT_TOKEN=your_token`

### "OPENAI_API_KEY not found"
→ Add to .env: `OPENAI_API_KEY=sk-...`

### Webhook not receiving messages
→ Run: `python telegram_webhook_setup.py` (option 1)

### Response too slow
→ Check OpenAI status, increase timeout in code

### Database lock error
→ Delete `ai_memory.db` and restart

## 📚 Documentation

- **Full Guide**: See `AI_AGENT_INTEGRATION_GUIDE.md`
- **Code Comments**: Well-documented in each file
- **Original Docs**: `ARCHITECTURE.md`, `MODULES_SUMMARY.md`

## 🎯 Next Steps

1. ✅ Setup .env with tokens
2. ✅ Run test: `python test_ai_integration.py`
3. ✅ Start server: `python run.py`
4. ✅ Setup webhook: `python telegram_webhook_setup.py`
5. ✅ Chat on Telegram!

## 💡 Tips

- **Debug Mode**: `export LOG_LEVEL=DEBUG && python run.py`
- **Polling Mode**: Use `telegram_webhook_setup.py` option 2
- **Memory Clear**: `python -c "asyncio.run(get_ai_integration().clear_conversation(user_id))"`
- **Custom Prompts**: Edit `ai_integration.py` to add system prompts

## 📞 Support

See detailed troubleshooting in `AI_AGENT_INTEGRATION_GUIDE.md`

---

**Made with ❤️ | Ready to deploy! 🚀**
