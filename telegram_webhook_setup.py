"""
Telegram Webhook Setup Tool
Use this to configure webhook URL for your Telegram bot
"""

import asyncio
import logging
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TelegramWebhookSetup:
    """Helper class to setup Telegram webhook"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def get_webhook_info(self) -> dict:
        """Get current webhook information"""
        try:
            response = requests.get(f"{self.base_url}/getWebhookInfo")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting webhook info: {e}")
            return None
    
    def set_webhook(self, webhook_url: str, allowed_updates: list = None) -> bool:
        """Set webhook URL for bot"""
        try:
            if allowed_updates is None:
                allowed_updates = ["message", "callback_query", "edited_message"]
            
            payload = {
                "url": webhook_url,
                "allowed_updates": allowed_updates,
                "drop_pending_updates": True
            }
            
            logger.info(f"Setting webhook to: {webhook_url}")
            logger.info(f"Allowed updates: {allowed_updates}")
            
            response = requests.post(f"{self.base_url}/setWebhook", json=payload)
            response.raise_for_status()
            
            data = response.json()
            if data.get("ok"):
                logger.info("✅ Webhook set successfully!")
                logger.info(f"Response: {data.get('description', 'OK')}")
                return True
            else:
                logger.error(f"❌ Failed to set webhook: {data.get('description', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error setting webhook: {e}")
            return False
    
    def delete_webhook(self) -> bool:
        """Delete webhook and switch to polling"""
        try:
            logger.info("Deleting webhook...")
            
            response = requests.post(f"{self.base_url}/deleteWebhook", json={"drop_pending_updates": True})
            response.raise_for_status()
            
            data = response.json()
            if data.get("ok"):
                logger.info("✅ Webhook deleted successfully!")
                logger.info("Bot will now use polling to receive messages")
                return True
            else:
                logger.error(f"❌ Failed to delete webhook: {data.get('description', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error deleting webhook: {e}")
            return False
    
    def get_me(self) -> dict:
        """Get bot information"""
        try:
            response = requests.get(f"{self.base_url}/getMe")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            return None


def print_webhook_info(info: dict):
    """Pretty print webhook information"""
    if not info or not info.get("ok"):
        logger.info("Could not retrieve webhook info")
        return
    
    result = info.get("result", {})
    logger.info("\n📡 Current Webhook Status:")
    logger.info(f"   URL: {result.get('url', 'Not set')}")
    logger.info(f"   Has Custom Certificate: {result.get('has_custom_certificate', False)}")
    logger.info(f"   Pending Update Count: {result.get('pending_update_count', 0)}")
    
    if result.get("ip_address"):
        logger.info(f"   Last IP Address: {result.get('ip_address')}")
    
    if result.get("last_error_date"):
        logger.info(f"   Last Error Time: {result.get('last_error_date')}")
        logger.info(f"   Last Error Message: {result.get('last_error_message', 'N/A')}")
    
    logger.info("")


def print_bot_info(info: dict):
    """Pretty print bot information"""
    if not info or not info.get("ok"):
        logger.info("Could not retrieve bot info")
        return
    
    result = info.get("result", {})
    logger.info("\n🤖 Bot Information:")
    logger.info(f"   ID: {result.get('id')}")
    logger.info(f"   First Name: {result.get('first_name')}")
    logger.info(f"   Username: @{result.get('username')}")
    logger.info(f"   Is Bot: {result.get('is_bot')}")
    logger.info("")


def main():
    """Main setup function"""
    logger.info("=" * 60)
    logger.info("🔧 Telegram Webhook Setup Tool")
    logger.info("=" * 60 + "\n")
    
    # Get bot token
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        logger.error("   Please set TELEGRAM_BOT_TOKEN in .env file")
        sys.exit(1)
    
    setup = TelegramWebhookSetup(bot_token)
    
    # Get bot info
    logger.info("📋 Retrieving bot information...")
    bot_info = setup.get_me()
    print_bot_info(bot_info)
    
    # Get current webhook status
    logger.info("📡 Checking current webhook status...")
    webhook_info = setup.get_webhook_info()
    print_webhook_info(webhook_info)
    
    # Menu
    while True:
        logger.info("Choose an option:")
        logger.info("  1 - Set webhook URL")
        logger.info("  2 - Delete webhook (switch to polling)")
        logger.info("  3 - Refresh webhook status")
        logger.info("  4 - Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            webhook_url = input("\nEnter webhook URL (e.g., https://example.com:8443/webhook/telegram): ").strip()
            
            if not webhook_url.startswith("http"):
                logger.error("❌ Invalid URL format. Must start with http:// or https://")
                continue
            
            confirm = input(f"\nConfirm setting webhook to:\n{webhook_url}\n(yes/no): ").strip().lower()
            if confirm == "yes":
                if setup.set_webhook(webhook_url):
                    logger.info("\n✅ Setup completed successfully!")
                    logger.info(f"Your bot is now listening on: {webhook_url}")
                    break
                else:
                    logger.error("Try again or check your bot token")
            else:
                logger.info("Cancelled")
        
        elif choice == "2":
            confirm = input("\nSwitch to polling mode? (yes/no): ").strip().lower()
            if confirm == "yes":
                if setup.delete_webhook():
                    logger.info("\n✅ Webhook deleted successfully!")
                    logger.info("Your bot will receive messages via polling")
                    break
                else:
                    logger.error("Failed to delete webhook. Try again")
            else:
                logger.info("Cancelled")
        
        elif choice == "3":
            logger.info("📡 Refreshing webhook status...")
            webhook_info = setup.get_webhook_info()
            print_webhook_info(webhook_info)
        
        elif choice == "4":
            logger.info("Goodbye!")
            break
        
        else:
            logger.error("❌ Invalid choice. Please enter 1-4")
        
        logger.info("")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n👋 Setup cancelled by user")
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
