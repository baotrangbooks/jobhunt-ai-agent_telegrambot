"""
Integration Test Script
Test AI Agent integration with Telegram Bot
"""

import asyncio
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()


async def test_imports():
    """Test if all modules can be imported"""
    logger.info("=" * 60)
    logger.info("🧪 Test 1: Import Modules")
    logger.info("=" * 60)
    
    try:
        logger.info("  Importing telegram_sender...")
        from telegram_sender import TelegramSender
        logger.info("  ✅ telegram_sender imported")
        
        logger.info("  Importing models...")
        from models import IncomingMessage
        logger.info("  ✅ models imported")
        
        logger.info("  Importing ai_integration...")
        from ai_integration import get_ai_integration, AIAgentIntegration
        logger.info("  ✅ ai_integration imported")
        
        logger.info("  Importing webhooks...")
        from webhooks import app
        logger.info("  ✅ webhooks imported")
        
        logger.info("\n✅ All modules imported successfully!\n")
        return True
        
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        logger.error(f"   Make sure all dependencies are installed: pip install -r requirements.txt")
        return False


async def test_env_variables():
    """Test if environment variables are set"""
    logger.info("=" * 60)
    logger.info("🧪 Test 2: Environment Variables")
    logger.info("=" * 60)
    
    import os
    
    checks = {
        "TELEGRAM_BOT_TOKEN": False,
        "OPENAI_API_KEY": False,
    }
    
    for var_name in checks:
        value = os.getenv(var_name)
        if value:
            masked = f"{value[:10]}...{value[-5:]}" if len(value) > 15 else value
            logger.info(f"  ✅ {var_name}: {masked}")
            checks[var_name] = True
        else:
            logger.error(f"  ❌ {var_name}: NOT SET")
    
    if not checks["OPENAI_API_KEY"]:
        logger.warning("  ⚠️ OpenAI API Key not set - AI agent won't work!")
    
    logger.info("")
    
    all_ok = checks["TELEGRAM_BOT_TOKEN"]
    return all_ok


async def test_ai_integration():
    """Test AI integration initialization"""
    logger.info("=" * 60)
    logger.info("🧪 Test 3: AI Integration")
    logger.info("=" * 60)
    
    try:
        from ai_integration import get_ai_integration
        
        logger.info("  Initializing AI integration...")
        ai = await get_ai_integration()
        
        if ai._initialized:
            logger.info("  ✅ AI integration initialized successfully")
            
            # Get stats
            stats = ai.get_conversation_stats(test_user_id=999)
            logger.info(f"  ✅ Conversation memory ready")
            
            logger.info("")
            return True
        else:
            logger.error("  ❌ AI integration failed to initialize")
            logger.error("     Check OpenAI API Key and internet connection")
            logger.info("")
            return False
            
    except Exception as e:
        logger.error(f"  ❌ AI integration test failed: {e}")
        import traceback
        traceback.print_exc()
        logger.info("")
        return False


async def test_ai_chat():
    """Test AI chat functionality"""
    logger.info("=" * 60)
    logger.info("🧪 Test 4: AI Chat (with AI Agent)")
    logger.info("=" * 60)
    
    try:
        from ai_integration import get_ai_integration
        
        logger.info("  Sending test message to AI agent...")
        logger.info("  User: 'Hello, what is 2+2?'")
        
        ai = await get_ai_integration()
        
        # Get response with timeout
        try:
            response = await asyncio.wait_for(
                ai.get_response(
                    user_id=999,
                    user_message="Hello, what is 2+2?",
                    timeout=20
                ),
                timeout=25
            )
            
            if response and not response.startswith("❌"):
                logger.info(f"  ✅ Response received:")
                logger.info(f"     {response[:200]}...")
                logger.info("")
                return True
            else:
                logger.error(f"  ❌ Error response: {response}")
                logger.info("")
                return False
                
        except asyncio.TimeoutError:
            logger.error("  ⏱️ Request timed out - AI agent taking too long")
            logger.error("     This might be normal if OpenAI API is slow")
            logger.info("")
            return False
            
    except Exception as e:
        logger.error(f"  ❌ Chat test failed: {e}")
        import traceback
        traceback.print_exc()
        logger.info("")
        return False


async def test_webhook_health():
    """Test webhook health endpoint"""
    logger.info("=" * 60)
    logger.info("🧪 Test 5: Webhook Health")
    logger.info("=" * 60)
    
    try:
        from webhooks import app
        from fastapi.testclient import TestClient
        
        logger.info("  Testing GET / endpoint...")
        client = TestClient(app)
        response = client.get("/")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"  ✅ Health check passed")
            logger.info(f"     {data.get('message')}")
            logger.info("")
            return True
        else:
            logger.error(f"  ❌ Health check failed: {response.status_code}")
            logger.info("")
            return False
            
    except Exception as e:
        logger.error(f"  ❌ Webhook test failed: {e}")
        logger.info("")
        return False


async def test_telegram_bot_token():
    """Test if bot token is valid"""
    logger.info("=" * 60)
    logger.info("🧪 Test 6: Telegram Bot Token")
    logger.info("=" * 60)
    
    try:
        import os
        import requests
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            logger.error("  ❌ Bot token not set")
            logger.info("")
            return False
        
        logger.info("  Validating bot token with Telegram API...")
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if data.get("ok"):
            result = data["result"]
            logger.info(f"  ✅ Bot token is valid")
            logger.info(f"     Bot: @{result['username']}")
            logger.info(f"     Name: {result['first_name']}")
            logger.info("")
            return True
        else:
            logger.error(f"  ❌ Bot token invalid: {data.get('description')}")
            logger.info("")
            return False
            
    except Exception as e:
        logger.error(f"  ❌ Token validation failed: {e}")
        logger.info("")
        return False


async def main():
    """Run all tests"""
    logger.info("\n")
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " " * 58 + "║")
    logger.info("║" + "  🤖 Telegram Bot + AI Agent Integration Tests".center(58) + "║")
    logger.info("║" + " " * 58 + "║")
    logger.info("╚" + "=" * 58 + "╝")
    logger.info("")
    
    results = {}
    
    # Run tests
    results["Imports"] = await test_imports()
    results["Environment"] = await test_env_variables()
    results["Telegram Token"] = await test_telegram_bot_token()
    results["AI Integration"] = await test_ai_integration()
    results["AI Chat"] = await test_ai_chat()
    results["Webhook Health"] = await test_webhook_health()
    
    # Summary
    logger.info("=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {status:10} - {test_name}")
    
    logger.info("")
    logger.info(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n✅ All tests passed! System is ready to use.")
        logger.info("\n👉 Next steps:")
        logger.info("   1. Set up webhook: python telegram_webhook_setup.py")
        logger.info("   2. Start server: python run.py")
        logger.info("   3. Chat with bot on Telegram!")
        return 0
    else:
        logger.error(f"\n❌ {total - passed} test(s) failed!")
        logger.error("\n👉 Failed tests require attention:")
        for test_name, result in results.items():
            if not result:
                logger.error(f"   - {test_name}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n\n❌ Tests cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
