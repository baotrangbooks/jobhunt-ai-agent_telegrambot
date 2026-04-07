## 📚 Telegram Bot Modules - Quick Reference Guide

### ✅ Tất cả 6 modules đã hoàn thành

#### 1️⃣ **accounts.py** (289 lines)
```python
# Quản lý multi-account & xác thực
manager = get_account_manager()
manager.add_account("bot1", token="...")
account = manager.resolve_account()
token = manager.get_bot_token("bot1")
```

**Tính năng:**
- ✅ Multi-account management
- ✅ Token validation via Telegram API
- ✅ Permission system
- ✅ Persistent JSON storage
- ✅ Account metadata
- ✅ Fallback to first active account

---

#### 2️⃣ **targets.py** (401 lines)
```python
# Phân tích & chuẩn hóa targets
parser = get_parser()
parsed = parser.parse_target("@username")
# Supports: IDs, usernames, prefixed, threads
```

**Tính năng:**
- ✅ Parse usernames (@name)
- ✅ Parse numeric IDs (123456789)
- ✅ Parse threads (chat_id/thread:456)
- ✅ Resolve usernames to IDs via API
- ✅ Detect chat type (private/group/supergroup/channel)
- ✅ Target validation & normalization

**Supported Formats:**
```
"123456789"              # Numeric ID
"@username"              # Username
"group:123456789"        # Prefixed format
"channel:-123456789"     # Channel with prefix
"123456789/thread:456"   # Thread format
```

---

#### 3️⃣ **runtime.py** (357 lines)
```python
# Runtime context: rate limiting, caching, retry
ctx = get_runtime_context()
ctx.wait_for_rate_limit()
ctx.set_cache("key", value)
ctx.get_cache("key")
```

**Tính năng:**
- ✅ Token bucket rate limiting (2 req/sec)
- ✅ LRU cache with TTL (default 1 hour)
- ✅ Exponential backoff retry decorator
- ✅ Per-account/per-bucket rate limiting
- ✅ Statistics tracking
- ✅ Cache hit rate monitoring

**Decorators:**
```python
@retry_with_backoff(max_attempts=3)
async def my_function():
    pass

@cache_result(ttl=3600)
def get_user_info(id):
    pass
```

---

#### 4️⃣ **utils.py** (520 lines)
```python
# Utilities: error handling, HTML, retry, validation
from utils import (
    retry_on_failure, is_html_parse_error,
    markdown_to_html, split_message,
    validate_chat_id, is_private_chat
)
```

**Tính năng:**
- ✅ Error detection (auth, rate limit, HTML, thread, etc)
- ✅ Exponential backoff retry decorator
- ✅ HTML ↔ Markdown conversion
- ✅ HTML sanitization for Telegram
- ✅ Message chunking (4096 char limit)
- ✅ Thread handling with fallback
- ✅ Chat type detection
- ✅ Validation functions

**Custom Exceptions:**
```python
TelegramAuthError          # 401
TelegramRateLimitError     # 429
TelegramHTMLParseError     # HTML parse failed
TelegramThreadNotFoundError # Thread not found
TelegramNetworkError       # Connection issues
```

---

#### 5️⃣ **setup.py** (340 lines)
```python
# Interactive setup wizard
wizard = SetupWizard()
config = wizard.start()  # Interactive prompts
# OR
config = await auto_setup()  # From env vars
```

**Tính năng:**
- ✅ Interactive setup wizard
- ✅ Token validation
- ✅ Bot info retrieval
- ✅ Policy configuration (PM, groups, channels)
- ✅ Admin ID management
- ✅ Webhook/polling configuration
- ✅ Connection testing
- ✅ Auto-setup from environment variables

**Interactive Steps:**
1. Enter bot token
2. Validate with Telegram API
3. Display bot name & username
4. Set policies (PM, groups, channels)
5. Set admin IDs
6. Configure webhook or polling
7. Save configuration

---

#### 6️⃣ **channel.py** (359 lines)
```python
# Main channel: routing, adapters, handlers
channel = get_channel()
await send_message(target, text, buttons=[[...]])
await edit_message(chat_id, message_id, text)

@on_text_message
async def handle_text(msg):
    pass

@on_callback_query
async def handle_button(msg):
    pass

@on_error
async def handle_error(error, msg):
    pass
```

**Tính năng:**
- ✅ Unified send/receive interface (adapter pattern)
- ✅ Message routing by type
- ✅ Handler registration & execution
- ✅ Rate limiting per account
- ✅ Account resolution
- ✅ Error handling
- ✅ Statistics tracking

**Supported Operations:**
```python
send_message(target, text, thread_id, media_url, buttons, text_mode)
edit_message(chat_id, message_id, text, buttons)
delete_message(chat_id, message_id)
react_message(chat_id, message_id, emoji)
```

**Message Types:**
- `text` - Regular text messages
- `media` - Media files (photo, video, etc)
- `callback` - Button callbacks
- `error` - Error handling

---

### 📊 Statistics & Monitoring

```python
from runtime import get_runtime_manager

manager = get_runtime_manager()

# Get stats for all contexts
stats = manager.get_all_stats()
# {
#   "requests_made": 150,
#   "cache_hits": 45,
#   "cache_misses": 30,
#   "cache_hit_rate": 60.0,
#   "rate_limit_hits": 2,
#   "cache_size": 45
# }

# Clear all caches
manager.clear_all_caches()
```

---

### 🔧 Configuration from Environment

```bash
# .env file
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_BOT_NAME=MyBot
TELEGRAM_ALLOW_PM=true
TELEGRAM_ALLOW_GROUPS=true
TELEGRAM_ALLOW_CHANNELS=false
TELEGRAM_WEBHOOK_URL=https://example.com/webhook
TELEGRAM_POLLING=false
```

```python
from setup import auto_setup

config = await auto_setup()
```

---

### 🚀 Complete Initialization Example

```python
import asyncio
from accounts import get_account_manager
from channel import get_channel, send_message
from setup import SetupWizard

async def main():
    # Setup wizard (if no config)
    wizard = SetupWizard()
    config = wizard.start() if not wizard.load_config() else wizard.load_config()
    
    # Add account
    manager = get_account_manager()
    manager.add_account("main", config.bot_token)
    
    # Get channel
    channel = get_channel()
    
    # Register handlers
    @channel.register_handler("text")
    async def handle_text(msg):
        print(f"Received: {msg.text}")
        await send_message(str(msg.chat_id), f"Echo: {msg.text}")
    
    # Start channel
    await channel.start()
    
    # Test
    result = await send_message(
        target="123456789",
        text="Hello!",
        buttons=[[{"text": "OK", "callback_data": "ok"}]]
    )
    print(f"✅ Message sent: {result}")

asyncio.run(main())
```

---

### 📈 Testing Examples

```python
from accounts import get_account_manager
from targets import get_parser
from runtime import get_runtime_context
from utils import validate_chat_id, is_private_chat

# Test 1: Account management
manager = get_account_manager()
manager.add_account("test", "123456:ABC...")

# Test 2: Target parsing
parser = get_parser()
parsed = parser.parse_target("@testuser")
assert parsed.is_valid

# Test 3: Runtime (rate limit + cache)
ctx = get_runtime_context()
ctx.set_cache("key", "value")
assert ctx.get_cache("key") == "value"

# Test 4: Utilities
assert validate_chat_id("123456789")
assert is_private_chat("123456789")
assert not is_private_chat("-123456789")
```

---

### 📝 Architecture Diagram

```
┌────────────────────────────────────────────┐
│  User Application                          │
└────────────────────────────────────────────┘
              ↓
┌────────────────────────────────────────────┐
│  channel.py (Main Channel)                 │
│  - send_message()                          │
│  - receive_message()                       │
│  - register_handler()                      │
└────────────────────────────────────────────┘
              ↓
┌────────────────────────────────────────────┐
│  Processing Layer                          │
│  ├─ targets.py (Parse targets)             │
│  ├─ accounts.py (Resolve account)          │
│  └─ utils.py (Error handling)              │
└────────────────────────────────────────────┘
              ↓
┌────────────────────────────────────────────┐
│  runtime.py (Context)                      │
│  ├─ Rate limiting                          │
│  ├─ Caching                                │
│  └─ Retry logic                            │
└────────────────────────────────────────────┘
              ↓
┌────────────────────────────────────────────┐
│  telegram_sender.py (API Wrapper)          │
│  - TelegramSender class                    │
│  - API method implementations              │
└────────────────────────────────────────────┘
              ↓
┌────────────────────────────────────────────┐
│  Telegram Bot API                          │
└────────────────────────────────────────────┘
```

---

### ✅ Implementation Checklist

- [x] `accounts.py` - 289 lines
- [x] `targets.py` - 401 lines
- [x] `runtime.py` - 357 lines
- [x] `utils.py` - 520 lines
- [x] `setup.py` - 340 lines
- [x] `channel.py` - 359 lines
- [x] `integration_example.py` - 350 lines
- [x] `ARCHITECTURE.md` - Comprehensive docs
- [x] All syntax checked ✅
- [x] Git committed ✅

**Total lines of code: 2,916 lines**

---

### 🎯 Next Steps (Optional)

1. Add database layer (SQLAlchemy)
2. Add webhook receiver integration
3. Add message persistence
4. Add monitoring/alerting
5. Add multilanguage support
6. Add command routing system
7. Add middleware system

---

**Status: ✅ COMPLETE**

Last updated: 2026-04-07
Commits: 2 (Initial + 6 Modules)
