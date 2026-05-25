"""
Telegram Bot with AI Agent Integration
Run this script to start the FastAPI webhook server
"""

import asyncio
import logging
import uvicorn
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import after loading env
from webhooks import app
from ai_integration import get_ai_integration


async def startup_event():
    """Initialize AI agent on startup"""
    logger.info("🚀 Initializing AI agent integration...")
    try:
        ai_integration = await get_ai_integration()
        if ai_integration._initialized:
            logger.info("✅ AI agent integration initialized successfully")
            stats = ai_integration.get_conversation_stats(0)
            logger.info(f"   Conversation memory ready")
        else:
            logger.warning("⚠️ AI agent integration failed to initialize")
    except Exception as e:
        logger.error(f"❌ Error initializing AI agent: {e}")


async def startup_task():
    """Run async startup tasks"""
    await startup_event()


@app.on_event("startup")
async def app_startup():
    """FastAPI startup event"""
    await startup_task()


@app.on_event("shutdown")
async def app_shutdown():
    """FastAPI shutdown event"""
    logger.info("🛑 Shutting down AI Telegram Bot...")


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("🤖 AI Telegram Bot with AI Agent Integration")
    logger.info("=" * 60)
    
    # Check environment variables
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        logger.error("   Please set TELEGRAM_BOT_TOKEN in .env file")
        return
    
    logger.info(f"✅ Bot token configured")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        logger.warning("⚠️ OPENAI_API_KEY not found - AI agent will not work")
        logger.warning("   Please set OPENAI_API_KEY in .env file for full functionality")
    else:
        logger.info("✅ OpenAI API configured")
    
    # Get server configuration
    host = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    port = int(os.getenv("WEBHOOK_PORT", "8008"))
    
    logger.info(f"\n📡 Starting webhook server on {host}:{port}")
    logger.info(f"   Webhook URL should be: http://<public_ip>:{port}/webhook/telegram")
    logger.info(f"   Zalo webhook URL should be: http://<public_ip>:{port}/webhook/zalo")
    logger.info("\n🔄 Available endpoints:")
    logger.info("   GET  /  - Health check")
    logger.info("   POST /webhook/telegram - Telegram webhook")
    logger.info("   POST /webhook/zalo - Zalo webhook")
    logger.info("\n💬 Chat interactions will be processed by AI agent")
    logger.info("=" * 60 + "\n")
    
    # Run Uvicorn
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("\n🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")


if __name__ == "__main__":
    main()
