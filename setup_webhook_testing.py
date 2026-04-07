#!/usr/bin/env python3
"""
Quick setup helper for Telegram webhook testing
Provides utilities to configure and test the webhook
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_step(step, text):
    """Print step"""
    print(f"\n[{step}] {text}")

def check_env_file():
    """Check if .env file exists and has token"""
    print_step("1", "Checking .env file")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("   ❌ .env file not found")
        print_step("1a", "Creating .env from .env.example")
        
        example_file = Path(".env.example")
        if example_file.exists():
            with open(example_file, 'r') as f:
                content = f.read()
            with open(env_file, 'w') as f:
                f.write(content)
            print("   ✅ .env created from template")
        else:
            print("   ❌ .env.example not found either")
            return False
    else:
        print("   ✅ .env file found")
    
    # Check for token
    with open(env_file, 'r') as f:
        content = f.read()
        if "your_telegram_bot_token" in content.lower():
            print("   ⚠️  TELEGRAM_BOT_TOKEN not configured")
            print("   Please edit .env and set your bot token")
            return False
        elif "TELEGRAM_BOT_TOKEN=" in content:
            print("   ✅ TELEGRAM_BOT_TOKEN is set")
            return True
    
    return True

def check_dependencies():
    """Check if dependencies are installed"""
    print_step("2", "Checking dependencies")
    
    required = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "httpx",
        "requests",
        "python_telegram_bot",
        "dotenv"
    ]
    
    missing = []
    for pkg in required:
        try:
            __import__(pkg.replace("-", "_").replace("_telegram_bot", "telegram"))
            print(f"   ✅ {pkg}")
        except ImportError:
            print(f"   ❌ {pkg}")
            missing.append(pkg)
    
    if missing:
        print(f"\n   Installing missing packages: {', '.join(missing)}")
        # Install missing packages
        cmd = [sys.executable, "-m", "pip", "install"] + missing
        subprocess.run(cmd)
        return True
    
    print("   ✅ All dependencies installed")
    return True

def show_quick_reference():
    """Show quick reference for testing"""
    print_header("📚 QUICK REFERENCE - Available Examples")
    
    examples = {
        "help": "Show this help menu",
        "Example 1": "Simple text message",
        "Example 2": "Message with retry config",
        "Example 3": "Message with inline buttons",
        "Example 4": "HTML formatted message",
        "Example 5": "Typing indicator",
        "Example 6": "Poll",
        "Example 7": "Edit message",
        "Example 8": "Pin message",
        "Example 9": "React with emoji",
        "Example 10": "Buttons with silent mode",
    }
    
    for cmd, desc in examples.items():
        print(f"  📢 Send to bot: \"{cmd}\"")
        print(f"     → {desc}\n")

def show_setup_instructions():
    """Show setup instructions"""
    print_header("🚀 SETUP INSTRUCTIONS")
    
    print("""
1. CONFIGURE ENVIRONMENT
   └─ Edit .env file with your TELEGRAM_BOT_TOKEN

2. START SERVER
   └─ Run: python main.py
   └─ Server will run on: http://localhost:8008

3. SETUP TELEGRAM WEBHOOK (NEW TERMINAL)
   
   For LOCAL TESTING (using ngrok):
   ├─ Install ngrok from: https://ngrok.com/download
   ├─ Run: ngrok http 8008
   └─ Copy the URL (e.g., https://abc123.ngrok.io)
   
   Set webhook with:
   └─ curl -X POST \\
        https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook \\
        -H 'Content-Type: application/json' \\
        -d '{
          "url": "https://abc123.ngrok.io/webhook/telegram"
        }'
   
   For PRODUCTION (using real domain):
   └─ Replace ngrok URL with your actual domain URL

4. TEST IN TELEGRAM
   └─ Open Telegram and message your bot
   └─ Send: "help" to see all commands
   └─ Send: "Example 1" to run first example

5. MONITOR LOGS
   └─ Watch your terminal for debug output
   └─ Server logs show which example is running
""")

def show_troubleshooting():
    """Show troubleshooting tips"""
    print_header("🔧 TROUBLESHOOTING")
    
    print("""
ISSUE: "Chat not found" error
Solution:
  • Make sure your chat ID is correct
  • Get your chat ID by messaging the bot with @username
  • Check it in the webhook logs

ISSUE: Webhook not receiving messages
Solution:
  • Verify webhook URL is set: 
    curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
  • Check ngrok is still running
  • Firewall might be blocking port 8008

ISSUE: "TELEGRAM_BOT_TOKEN not provided"
Solution:
  • Edit .env and add your bot token
  • Format: TELEGRAM_BOT_TOKEN=123456789:ABCDefGhIjKlMnoP
  • Get token from @BotFather on Telegram

ISSUE: Examples not executing
Solution:
  • Check example name spelling (must match exactly)
  • Use "Example 1" not "example 1"
  • Watch logs for error messages
  • Make sure bot token is valid

ISSUE: Button clicks not working yet
Solution:
  • Current implementation shows callback_data
  • Can be extended to handle button actions
  • See WEBHOOK_TESTING_GUIDE.md for details
""")

def show_file_structure():
    """Show project structure"""
    print_header("📁 PROJECT FILES")
    
    files = {
        "Core":
            ["telegram_sender.py - Main TelegramSender class",
             "webhooks.py - FastAPI webhook with examples",
             "models.py - Pydantic data models"],
        "Testing":
            ["telegram_sender_example.py - Standalone examples",
             "test_telegram_sender.py - Unit tests"],
        "Documentation":
            ["TELEGRAM_SENDER_README.md - API reference",
             "WEBHOOK_TESTING_GUIDE.md - Testing guide",
             "GETTING_STARTED.md - Quick start",
             "README.md - Project overview"],
        "Configuration":
            [".env - Your environment variables (keep secret!)",
             ".env.example - Template",
             "requirements.txt - Python dependencies",
             "main.py - FastAPI entry point"]
    }
    
    for category, items in files.items():
        print(f"\n  {category}:")
        for item in items:
            print(f"    • {item}")

def main():
    """Main entry point"""
    print_header("🤖 Telegram Webhook Testing Setup Helper")
    
    # Check prerequisites
    env_ok = check_env_file()
    deps_ok = check_dependencies()
    
    if not env_ok:
        print("\n⚠️  Please configure .env file first!")
        print("Edit .env and set your TELEGRAM_BOT_TOKEN")
        return
    
    # Show information
    show_quick_reference()
    show_setup_instructions()
    show_file_structure()
    show_troubleshooting()
    
    # Final message
    print_header("✅ READY TO TEST!")
    print("""
Next steps:
1. Edit .env with your TELEGRAM_BOT_TOKEN (if not done)
2. Run: python main.py
3. In new terminal: ngrok http 8008
4. Setup webhook with ngrok URL
5. Send "help" to your bot in Telegram
6. Try "Example 1" to start testing!

For detailed info, see: WEBHOOK_TESTING_GUIDE.md
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelling setup")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
