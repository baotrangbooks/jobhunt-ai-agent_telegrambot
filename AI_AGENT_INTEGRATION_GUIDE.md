# 🤖 Telegram Bot + AI Agent Integration Guide

Hướng dẫn tích hợp Telegram Bot với AI Chatbot Agent

## 📋 Mục lục

1. [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
2. [Cài đặt](#cài-đặt)
3. [Cấu hình](#cấu-hình)
4. [Khởi chạy](#khởi-chạy)
5. [Kiểm tra](#kiểm-tra)
6. [Cách hoạt động](#cách-hoạt-động)
7. [Xử lý sự cố](#xử-lý-sự-cố)

---

## 🔧 Yêu cầu hệ thống

- Python 3.11+
- Telegram Bot Token
- OpenAI API Key
- Git (để clone AI agent assistant)

### Packages chính

```
fastapi>=0.100.0
uvicorn>=0.23.0
python-telegram-bot>=20.0
langchain>=1.2.13
langchain-openai>=1.1.11
langgraph>=1.1.3
python-dotenv>=1.2.2
```

---

## 📦 Cài đặt

### 1. Clone hoặc có sẵn hai dự án

```bash
# Telegram Bot (dự án hiện tại)
cd /home/youruser/AI-Projects/telegram-bot

# AI Agent Assistant (nằm song song)
cd /home/youruser/AI-Projects/ai-agent-assistant
```

### 2. Tạo virtual environment cho Telegram Bot

```bash
cd C:\Users\Admin\AI-Projects\telegram-bot
python -m venv .venv
```

- Windows:
  ```powershell
  .\.venv\Scripts\activate
  ```
- Ubuntu/Linux:
  ```bash
  source .venv/bin/activate
  ```

### 3. Cài đặt dependencies

```bash
pip install fastapi uvicorn python-telegram-bot langchain-openai langgraph python-dotenv requests
```

### 4. Cài đặt AI Agent Assistant (nếu chưa có)

```bash
cd /home/youruser/AI-Projects/ai-agent-assistant
pip install -e .
```

> Nếu bạn deploy lên server Ubuntu/Linux và `ai-agent-assistant` không nằm song song với `telegram-bot`, cấu hình biến môi trường `AI_AGENT_ASSISTANT_PATH` trỏ tới thư mục gốc của `ai-agent-assistant`.

> Ví dụ trên Ubuntu:
> ```bash
> export AI_AGENT_ASSISTANT_PATH="/home/youruser/AI-Projects/ai-agent-assistant"
> ```

---

## ⚙️ Cấu hình

### 1. Tạo Bot Telegram

1. Mở Telegram và tìm **@BotFather**
2. Gửi `/newbot`
3. Chọn tên bot (ví dụ: "MyAIBot")
4. Chọn username (ví dụ: "my_ai_bot_123")
5. BotFather sẽ cấp **Bot Token** - lưu lại

### 2. Tạo tệp `.env`

Tạo file `.env` trong `telegram-bot` directory:

```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_BOT_NAME=MyAIBot

# OpenAI Configuration  
OPENAI_API_KEY=your_openai_api_key_here

# Webhook Configuration
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8000
WEBHOOK_URL=https://your-domain.com:8000/webhook/telegram

# AI Agent Configuration
AI_MEMORY_DB=ai_memory.db
```

**Thay thế:**
- `your_bot_token_here` - Token từ BotFather
- `your_openai_api_key_here` - API Key từ OpenAI
- `https://your-domain.com` - Domain công khai của server

### 3. Verify Environment Variables

```bash
# Test load environment
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(f'Bot Token: {os.getenv(\"TELEGRAM_BOT_TOKEN\")[:20]}...')"
```

---

## 🚀 Khởi chạy

### Option 1: Chế độ Development (Local)

Chạy webhook server trên Ubuntu/Linux:

```bash
cd /home/youruser/AI-Projects/telegram-bot
source .venv/bin/activate
python run.py
```

Nếu bạn dùng Windows thì:

```powershell
cd C:\Users\Admin\AI-Projects\telegram-bot
.\.venv\Scripts\activate
python run.py
```

**Output:**
```
============================================================
🤖 AI Telegram Bot with AI Agent Integration
============================================================
✅ Bot token configured
✅ OpenAI API configured

📡 Starting webhook server on 0.0.0.0:8000
   Webhook URL should be: http://<public_ip>:8000/webhook/telegram
   
🔄 Available endpoints:
   GET  /  - Health check
   POST /webhook/telegram - Telegram webhook
   POST /webhook/zalo - Zalo webhook

💬 Chat interactions will be processed by AI agent
============================================================

INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Option 2: Chế độ Production (Public Webhook)

Để Telegram tương tác với bot:

1. **Thiết lập Domain + SSL**
   - Cần domain công khai với SSL certificate
   - Ví dụ: `https://mybot.example.com`

2. **Setup Webhook**
   ```bash
   python telegram_webhook_setup.py
   ```
   
   Menu:
   ```
   Choose an option:
     1 - Set webhook URL
     2 - Delete webhook (switch to polling)
     3 - Refresh webhook status
     4 - Exit
   
   Enter your choice (1-4): 1
   Enter webhook URL: https://mybot.example.com:8000/webhook/telegram
   ```

3. **Chạy Server trên Domain**
   ```bash
   python run.py
   ```
   
   Server sẽ lắng nghe trên port 8000

---

## ✅ Kiểm tra

### 1. Health Check

```bash
# Check server đang chạy
curl http://localhost:8000/

# Response:
# {"message":"AI Chatbot Backend is running!"}
```

### 2. Test Chat

Mở Telegram và nhắn tin đến bot của bạn:

```
User: Hello, what's your name?
Bot: [AI response từ agent]

User: What is 2+2?
Bot: [AI response từ agent]

User: Tell me a joke
Bot: [AI response từ agent]
```

### 3. Test Examples (Optional)

Nhắn những commands sau để test các ví dụ cơ bản:

```
- help (xem danh sách examples)
- example 1 (simple message)
- example 3 (buttons)
- example 6 (poll)
```

### 4. Xem Logs

Logs được in ra console và cho thấy:

```
[AI Agent] Getting response for user 123456789: Hello
[AI Agent] Response: Hi! I'm an AI assistant...
AI message sent to Telegram successfully
```

---

## 🔄 Cách hoạt động

### Message Flow

```
┌─────────────┐
│   User      │
│   (Telegram)│
└──────┬──────┘
       │ (sends message)
       ▼
┌─────────────────────────────────────┐
│  telegram_webhook (POST handler)    │
├─────────────────────────────────────┤
│  - Parse incoming Telegram update   │
│  - Extract text, user_id, etc.      │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│   process_with_ai()                 │
├─────────────────────────────────────┤
│  - Check if "help" or "example X"   │
│  - If yes: run example handler      │
│  - If no: call AI agent             │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  ai_integration.get_response()      │
├─────────────────────────────────────┤
│  - Get conversation history         │
│  - Call AI agent (OpenAI + tools)   │
│  - Stream/process response          │
│  - Store in memory                  │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  telegram_sender.send_message()     │
├─────────────────────────────────────┤
│  - Split if message > 4096 chars    │
│  - Send to Telegram API             │
│  - Handle retries                   │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────┐
│   Telegram  │
│   API       │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   User      │
│   (receives)│
└─────────────┘
```

### Conversation Memory

- **Per-User Memory**: Mỗi user ID có conversation history riêng
- **Persistent**: Được lưu trong `ai_memory.db` (SQLite)
- **Auto-Loaded**: Lịch sử được tự động load khi user gửi tin nhắn
- **Context-Aware**: AI agent sử dụng lịch sử để trả lời phù hợp

### Rate Limiting & Retry

- **Rate Limit**: 2 requests/sec per account (configurable)
- **Retry Strategy**: Exponential backoff với max 3 lần thử
- **Message Chunking**: Tự động split message nếu > 4096 ký tự

---

## 🐛 Xử lý sự cố

### Lỗi: "TELEGRAM_BOT_TOKEN not found"

**Nguyên nhân:** Chưa set biến môi trường

**Giải pháp:**
```bash
# Kiểm tra .env tồn tại
dir .env

# Kiểm tra nội dung
cat .env

# Restart server
python run.py
```

### Lỗi: "OPENAI_API_KEY not found"

**Nguyên nhân:** Chưa set OpenAI API Key

**Giải pháp:**
1. Thêm vào `.env`:
   ```
   OPENAI_API_KEY=sk-...your-key...
   ```
2. Restart server

### Webhook không nhận tin nhắn

**Nguyên nhân:** Webhook chưa được setup trên Telegram API

**Giải pháp:**
```bash
# Run setup tool
python telegram_webhook_setup.py

# Chọn option 1 để set URL
# Enter URL: https://your-domain.com:8000/webhook/telegram
```

### Response quá lâu

**Nguyên nhân:** AI agent xử lý lâu

**Giải pháp:**
- Kiểm tra OpenAI status
- Tăng timeout trong `ai_integration.get_response()` nếu cần
- Kiểm tra internet connection

### Database Lock Error

**Nguyên nhân:** SQLite database bị lock

**Giải pháp:**
```bash
# Xóa file ai_memory.db để reset
rm ai_memory.db

# Restart server - sẽ tạo mới
python run.py
```

---

## 📊 Monitoring

### Xem Conversation Stats

```python
from ai_integration import get_ai_integration
import asyncio

async def check_stats():
    ai = await get_ai_integration()
    stats = ai.get_conversation_stats(user_id=123456789)
    print(f"User stats: {stats}")

asyncio.run(check_stats())
```

Output:
```
User stats: {
    'user_id': 123456789,
    'total_messages': 42,
    'user_messages': 21,
    'assistant_messages': 21
}
```

### Clear User Conversation

```python
async def clear_chat():
    ai = await get_ai_integration()
    ai.clear_conversation(user_id=123456789)
    print("Conversation cleared")

asyncio.run(clear_chat())
```

---

## 🎯 Tiếp theo

### Mở rộng chức năng

1. **Custom Tools**
   - Thêm tools để AI agent có thể gọi (web search, database, etc.)

2. **User Authentication**
   - Validate users trước khi trả lời

3. **Bot Commands**
   - `/start` - welcome message
   - `/help` - show commands
   - `/clear` - clear conversation
   - `/stats` - show conversation stats

4. **Admin Controls**
   - `/admin_stats` - view all users
   - `/broadcast <message>` - send to all users

5. **Webhooks cho các nền tảng khác**
   - Zalo (đã setup)
   - WhatsApp
   - Discord
   - Slack

---

## 💡 Tips & Tricks

### Debug Mode

```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG
python run.py
```

### Test Locally (Polling Mode)

Nếu không có domain công khai, dùng polling thay webhook:

```python
# main_polling.py
from telegram import Bot

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
# Implement polling loop
```

### Custom AI Prompts

Sửa trong `ai_integration.py` để thêm system prompts:

```python
system_prompt = """
You are a helpful AI assistant that helps users with...
Focus on being concise and helpful.
"""
```

### Performance Optimization

- Increase `recursion_limit` cho complex tasks
- Adjust `temperature` parameter (0 = deterministic, 1 = creative)
- Enable caching để tránh re-compute

---

## 📞 Support

### Logs Location

- Console: Real-time output when running
- File: `debug.log` (if configured)
- Database: `ai_memory.db` (SQLite)

### Common Commands

```bash
# View logs in real-time
tail -f debug.log

# Check running processes
ps aux | grep python

# Kill process
pkill -f "python run.py"

# Request timeout adjustment
# Edit ai_integration.py line ~180:
# timeout=60  (increase for slower responses)
```

---

**Bạn đã sẵn sàng! Chat với bot của bạn ngay bây giờ! 🚀**
