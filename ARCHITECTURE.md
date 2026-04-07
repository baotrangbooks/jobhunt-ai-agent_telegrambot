# 📦 Telegram Bot Architecture - 6 Core Modules

## 概述 (Overview)

Đây là bản Python rewrite của extension Telegram TypeScript với 6 module chính tương tự cấu trúc trong `send.ts`, `accounts.ts`, `targets.ts`, `channel.ts`, `setup-core.ts`, và `runtime.ts`.

```
┌─────────────────────────────────────────────────────────────┐
│           Telegram Bot Integration Layer                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│    Channel (channel.py)                                    │
│    ├─ send_message()                                       │
│    ├─ edit_message()                                       │
│    ├─ delete_message()                                     │
│    └─ register_handler()                                   │
│                ↓                                            │
│    ┌────────────────────────────────────────────────────┐  │
│    │ Adapter Layer                                      │  │
│    ├────────────────────────────────────────────────────┤  │
│    │  • TelegramChannelAdapter                          │  │
│    │  • Rate limiting (runtime.py)                      │  │
│    │  • Caching (runtime.py)                            │  │
│    └────────────────────────────────────────────────────┘  │
│                ↓                                            │
│    ┌────────────────────────────────────────────────────┐  │
│    │ Processing Layer                                   │  │
│    ├────────────────────────────────────────────────────┤  │
│    │  • Target parsing (targets.py)                     │  │
│    │  • Account resolution (accounts.py)                │  │
│    │  • Error handling (utils.py)                       │  │
│    │  • Retry logic (utils.py)                          │  │
│    └────────────────────────────────────────────────────┘  │
│                ↓                                            │
│    ┌────────────────────────────────────────────────────┐  │
│    │ API Layer                                          │  │
│    ├────────────────────────────────────────────────────┤  │
│    │  • TelegramSender (telegram_sender.py)             │  │
│    │  • Telegram Bot API                                │  │
│    └────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 1️⃣ **accounts.py** - Account Management & Authentication

### Mục đích
Quản lý multiple bot tokens, xác thực, và quyền truy cập (tương tự `accounts.ts`)

### Thành phần chính
```python
@dataclass
class TelegramAccount:
    """Telegram account configuration"""
    id: str                         # Account ID
    token: str                      # Bot token
    bot_name: str                   # Bot name
    bot_username: str               # Bot username
    is_active: bool                 # Active status
    permissions: List[str]          # Permissions ["send_message", "edit_message", ...]
    metadata: Dict[str, Any]        # Custom metadata

class TelegramAccountManager:
    """Manage multiple Telegram accounts"""
    - add_account(account_id, token) -> bool
    - get_account(account_id) -> TelegramAccount
    - get_bot_token(account_id) -> str
    - validate_token(token) -> bool
    - list_accounts() -> List[TelegramAccount]
    - has_permission(account_id, permission) -> bool
    - resolve_account(account_id=None) -> TelegramAccount  # Fallback logic
```

### Sử dụng
```python
from accounts import get_account_manager

manager = get_account_manager()

# Add account
manager.add_account(
    account_id="main_bot",
    token="123456:ABC-DEF...",
    permissions=["send_message", "edit_message"]
)

# Get token
token = manager.get_bot_token("main_bot")

# Resolve account (with fallback)
account = manager.resolve_account()  # Gets first active if not specified
```

### Features
- ✅ Multi-account management
- ✅ Token validation
- ✅ Permission checking
- ✅ Persistent storage (JSON)
- ✅ Account metadata
- ✅ Fallback to first active account

---

## 2️⃣ **targets.py** - Target Parsing & Normalization

### Mục đích
Parse chat IDs, usernames, group IDs, thread IDs từ user input (tương tự `targets.ts`)

### Thành phần chính
```python
@dataclass
class ParsedTarget:
    chat_id: str
    username: Optional[str]
    thread_id: Optional[int]
    chat_type: ChatType  # "private", "group", "supergroup", "channel"
    is_valid: bool
    error: Optional[str]

class TargetParser:
    """Parse and normalize Telegram targets"""
    - parse_target(target: str) -> ParsedTarget
    - normalize_chat_id(chat_id: Any) -> str
    - extract_thread_id(target: str) -> Optional[int]
    - validate_target(target: str) -> bool
    - is_username(target: str) -> bool
    - is_chat_id(target: str) -> bool
    - resolve_username_to_id(username: str) -> Optional[str]
    - get_chat_type_from_id(chat_id: str) -> ChatType
```

### Sử dụng
```python
from targets import get_parser

parser = get_parser()

# Parse different formats
parsed = parser.parse_target("@username")         # Username
parsed = parser.parse_target("123456789")         # Numeric ID
parsed = parser.parse_target("group:-123456789")  # Prefixed format
parsed = parser.parse_target("123/thread:456")    # With thread

# Validate
is_valid = parser.validate_target("@username")

# Extract thread
thread_id = parser.extract_thread_id("123456789/thread:456")
```

### Supported Formats
- Numeric IDs: `"123456789"`, `"-123456789"`
- Usernames: `"@username"`, `"username"`
- Prefixed: `"group:123"`, `"channel:@name"`, `"supergroup:-123"`
- With thread: `"123456789/thread:456"`
- Inline thread: `"123456789 thread:456"`

---

## 3️⃣ **runtime.py** - Runtime & Context Integration

### Mục đích
Provide context cho API calls, rate limiting, caching (tương tự `runtime.ts`)

### Thành phần chính
```python
class TelegramRuntimeContext:
    """Runtime context for API operations"""
    - wait_for_rate_limit(bucket: str) -> float
    - get_cache(key: str) -> Optional[Any]
    - set_cache(key: str, value: Any) -> None
    - clear_cache() -> None
    - get_stats() -> Dict[str, Any]

@dataclass
class RateLimitConfig:
    requests_per_second: float = 2.0
    burst_size: int = 10

@dataclass
class CacheConfig:
    enabled: bool = True
    ttl_seconds: int = 3600
    max_items: int = 1000

def retry_with_backoff(config: RetryConfig):
    """Decorator for exponential backoff retry"""
    
@cache_result(ttl=3600)
def my_function():
    """Decorator for caching function results"""
```

### Sử dụng
```python
from runtime import get_runtime_context, retry_with_backoff

context = get_runtime_context()

# Rate limiting
delay = context.wait_for_rate_limit()

# Caching
context.set_cache("key", value)
cached = context.get_cache("key")

# Statistics
stats = context.get_stats()
# {"requests_made": 100, "cache_hit_rate": 75.5, ...}

# Retry decorator
@retry_with_backoff(max_attempts=3, base_delay=0.5)
async def my_api_call():
    pass

# Cache decorator
@cache_result(ttl=3600)
def get_user_info(user_id):
    return fetch_user(user_id)
```

### Features
- ✅ Token bucket rate limiting
- ✅ LRU caching with TTL
- ✅ Exponential backoff retry
- ✅ Statistics tracking
- ✅ Per-account rate limiting

---

## 4️⃣ **utils.py** - Utilities & Error Handling

### Mục đích
Common utilities từ `send.ts` - retry, HTML parsing, thread handling, error detection

### Thành phần chính
```python
# Error detection
- is_auth_error(error)
- is_rate_limit_error(error)
- is_html_parse_error(error)
- is_thread_not_found_error(error)
- is_recoverable_error(error)

# Retry decorator
@retry_on_failure(max_attempts=3, base_delay=0.5)
async def my_function():
    pass

# HTML utilities
- markdown_to_html(text) -> str
- html_to_plain_text(html) -> str
- sanitize_html(html) -> str
- strip_html_tags(html) -> str

# Thread handling
- strip_thread_id(target: str) -> str
- with_thread_fallback(func)  # Decorator

# Text utilities
- split_message(text: str, max_length: int) -> List[str]
- truncate_text(text: str, max_length: int) -> str

# Validation
- validate_chat_id(chat_id: str) -> bool
- validate_username(username: str) -> bool
- is_private_chat(chat_id: str) -> bool
- is_group_chat(chat_id: str) -> bool
- is_channel_chat(chat_id: str) -> bool
```

### Sử dụng
```python
from utils import (
    retry_on_failure, is_html_parse_error, 
    markdown_to_html, split_message
)

# Retry with backoff
@retry_on_failure(max_attempts=3, retry_on=is_recoverable_error)
async def send_message():
    pass

# HTML conversion
html = markdown_to_html("**bold** *italic* `code`")

# Split long messages
chunks = split_message(long_text, max_length=4096)

# Error handling
try:
    send_api_call()
except Exception as e:
    if is_html_parse_error(e):
        # Fallback to plain text
        pass
```

### Features
- ✅ Comprehensive error detection
- ✅ HTML/Markdown conversion
- ✅ Exponential backoff retry
- ✅ Thread fallback handling
- ✅ Message chunking
- ✅ Chat type detection

---

## 5️⃣ **setup.py** - Configuration & Setup Wizard

### Mục đích
Interactive setup wizard cho bot token, policies, allowlists (tương tự `setup-core.ts`)

### Thành phần chính
```python
@dataclass
class TelegramConfig:
    bot_token: str
    allow_pm: bool = True
    allow_groups: bool = True
    allow_channels: bool = False
    admin_ids: List[int] = None
    webhook_url: Optional[str] = None
    polling_enabled: bool = False

class SetupWizard:
    """Interactive setup wizard"""
    - start() -> TelegramConfig              # Interactive setup
    - load_config() -> TelegramConfig
    - save_config(config) -> bool
    - test_connection(config) -> bool
    - test_webhook(config) -> bool

async def auto_setup(config_dir: str) -> TelegramConfig
    """Auto-setup from environment variables"""
```

### Sử dụng
```python
from setup import SetupWizard, auto_setup

# Interactive setup
wizard = SetupWizard()
config = wizard.start()

# Or auto-setup from env vars
# TELEGRAM_BOT_TOKEN=...
# TELEGRAM_WEBHOOK_URL=...
config = await auto_setup()

# Test connection
if wizard.test_connection(config):
    print("✅ Bot connected")

# Test webhook
if wizard.test_webhook(config):
    print("✅ Webhook working")
```

### Interactive Steps
1. Prompt for bot token
2. Validate token with Telegram API
3. Get bot name & username
4. Set policies (PM, groups, channels)
5. Set admin IDs
6. Configure webhook/polling
7. Save configuration

---

## 6️⃣ **channel.py** - Channel Logic & Core Integration

### Mục đích
"Trái tim" của extension - kết nối core, routing messages, adapters (tương tự `channel.ts`)

### Thành phần chính
```python
@dataclass
class OutgoingMessage:
    target: str
    text: str
    thread_id: Optional[int] = None
    media_url: Optional[str] = None
    buttons: Optional[List]
    text_mode: str = "markdown"  # or "html"
    silent: bool = False

@dataclass
class IncomingMessage:
    message_id: int
    chat_id: str
    user_id: int
    text: str
    message_type: str = "text"  # text, media, callback

class TelegramChannel:
    """Main channel for all operations"""
    - send_via_channel(message: OutgoingMessage) -> Dict
    - receive_message(message: IncomingMessage)
    - register_handler(message_type: str, handler)
    - unregister_handler(message_type: str, handler)
    - is_connected() -> bool
    - start() -> None
    - stop() -> None

# Convenience functions
- send_message(target, text, ...) -> Dict
- edit_message(chat_id, message_id, text)
- delete_message(chat_id, message_id)
- react_message(chat_id, message_id, emoji)

# Decorators
@on_text_message
def handle_text(message): pass

@on_callback_query
def handle_callback(message): pass

@on_error
def handle_error(error, message): pass
```

### Sử dụng
```python
from channel import get_channel, send_message, on_text_message

# Get channel instance
channel = get_channel()

# Send message
result = await send_message(
    target="@username",
    text="Hello!",
    buttons=[[{"text": "OK", "callback_data": "ok"}]]
)

# Register handlers
@on_text_message
async def handle_text(message):
    print(f"Got: {message.text}")

@on_callback_query
async def handle_button(message):
    print(f"Button clicked: {message.text}")

# Start/stop channel
await channel.start()
# ... do stuff ...
await channel.stop()
```

### Features
- ✅ Adapter pattern for send/receive
- ✅ Message routing with type
- ✅ Handler registration
- ✅ Error handling
- ✅ Rate limiting integration
- ✅ Account resolution

---

## 🔗 Integration Flow

```
User Code
   ↓
Channel.send_message(target, text)
   ↓
TargetParser.parse_target(target)
   ↓
AccountManager.resolve_account()
   ↓
RuntimeContext.wait_for_rate_limit()
   ↓
TelegramSender.send_message()
   ↓
Telegram Bot API
   ↓
Response → RuntimeContext.cache()
   ↓
Return to User
```

## 📋 Complete Example

```python
import asyncio
from accounts import get_account_manager
from targets import get_parser
from channel import get_channel, send_message
from setup import SetupWizard
from utils import retry_on_failure

class MyBot:
    async def initialize(self):
        # Step 1: Setup
        wizard = SetupWizard()
        config = wizard.load_config()
        if not config:
            config = wizard.start()
        
        # Step 2: Add account to manager
        manager = get_account_manager()
        manager.add_account("main", config.bot_token)
        
        # Step 3: Get channel
        channel = get_channel()
        channel.register_handler("text", self.handle_text)
        await channel.start()
        
    async def handle_text(self, message):
        # Parse target
        parser = get_parser()
        parsed = parser.parse_target(f"@{message.username}")
        
        # Send response
        result = await send_message(
            target=str(message.chat_id),
            text=f"Echo: {message.text}"
        )
        
        if result.get("ok"):
            print(f"✅ Message sent: {result['message_id']}")

async def main():
    bot = MyBot()
    await bot.initialize()
    # Keep running...

asyncio.run(main())
```

---

## 📊 Statistics & Monitoring

```python
from runtime import get_runtime_manager

manager = get_runtime_manager()
stats = manager.get_all_stats()

print("Runtime Statistics:")
print(f"  Requests Made: {stats['requests_made']}")
print(f"  Cache Hit Rate: {stats['cache_hit_rate']:.1f}%")
print(f"  Rate Limit Hits: {stats['rate_limit_hits']}")
```

---

## ✅ Checklist

- [x] **accounts.py** - Multi-account management
- [x] **targets.py** - Target parsing & normalization
- [x] **runtime.py** - Rate limiting & caching context
- [x] **utils.py** - Error handling & utilities
- [x] **setup.py** - Configuration & setup wizard
- [x] **channel.py** - Channel integration
- [x] **integration_example.py** - Complete examples
- [x] **ARCHITECTURE.md** - This documentation

---

## 🚀 Next Steps

1. Test individual modules with `integration_example.py`
2. Integrate with existing webhook system in `webhooks.py`
3. Add database layer for persistent storage
4. Implement webhook receiver for incoming messages
5. Add monitoring & alerting

---

Last updated: 2026-04-07
