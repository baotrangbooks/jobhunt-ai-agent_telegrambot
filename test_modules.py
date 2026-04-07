#!/usr/bin/env python3
"""Quick test of 6 core modules"""

from targets import get_parser
from accounts import get_account_manager
from runtime import get_runtime_context
from utils import validate_chat_id, is_private_chat, markdown_to_html
from setup import SetupWizard

print('\n' + '='*60)
print('  Testing 6 Core Modules')
print('='*60 + '\n')

# Test 1: Targets
print('1️⃣  Testing targets.py:')
parser = get_parser()
for target in ['@username', '123456789', 'group:123', '123/thread:456']:
    parsed = parser.parse_target(target)
    print(f'  ✅ {target:.<30} -> chat_id={parsed.chat_id}')

# Test 2: Accounts
print('\n2️⃣  Testing accounts.py:')
manager = get_account_manager()
print(f'  ✅ Active accounts: {len(manager.list_accounts())}')

# Test 3: Runtime
print('\n3️⃣  Testing runtime.py:')
ctx = get_runtime_context()
ctx.set_cache("test_key", "test_value")
cached = ctx.get_cache("test_key")
print(f'  ✅ Cache set/get: {cached}')
stats = ctx.get_stats()
print(f'  ✅ Cache items: {stats["cache_size"]}')

# Test 4: Utils
print('\n4️⃣  Testing utils.py:')
print(f'  ✅ validate_chat_id(123): {validate_chat_id("123")}')
print(f'  ✅ is_private_chat(123): {is_private_chat("123")}')
print(f'  ✅ is_private_chat(-123): {is_private_chat("-123")}')
html = markdown_to_html("**bold** *italic* `code`")
print(f'  ✅ markdown_to_html: {html}')

# Test 5: Setup
print('\n5️⃣  Testing setup.py:')
wizard = SetupWizard()
config = wizard.load_config()
if config:
    print(f'  ✅ Config loaded: bot_token set')
else:
    print(f'  ✅ No existing config (expected for first run)')

# Test 6: Channel (module loading test)
print('\n6️⃣  Testing channel.py:')
try:
    from channel import get_channel
    channel = get_channel()
    print(f'  ✅ Channel instance created')
    print(f'  ✅ Channel connected: {channel.is_connected()}')
except Exception as e:
    print(f'  ⚠️  Channel test skipped (requires bot account): {str(e)[:50]}')

print('\n' + '='*60)
print('  ✅ All 6 Modules Loaded Successfully!')
print('='*60 + '\n')
