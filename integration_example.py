"""
Integration Example and Documentation
Hướng dẫn tích hợp tất cả 6 modules chính
"""

import asyncio
import logging
from pathlib import Path

# Import all modules
from accounts import get_account_manager
from targets import get_parser
from runtime import get_runtime_context, get_runtime_manager
from setup import SetupWizard, TelegramConfig, auto_setup
from channel import get_channel, send_message, on_text_message, OutgoingMessage
from utils import is_private_chat, validate_chat_id, retry_on_failure

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TelegramBotIntegration:
    """
    Complete integration of all Telegram modules
    Demonstrates how to use all 6 components together
    """

    def __init__(self, config_dir: str = ".config"):
        self.config_dir = Path(config_dir)
        self.account_manager = get_account_manager()
        self.parser = get_parser()
        self.runtime = get_runtime_context()
        self.channel = get_channel()
        self.setup_wizard = SetupWizard(config_dir)

        # Register message handlers
        self.channel.register_handler("text", self._handle_text_message)
        self.channel.register_handler("callback", self._handle_callback)
        self.channel.register_handler("error", self._handle_error)

    async def initialize(self) -> bool:
        """
        Initialize bot with full setup
        1. Load config or setup wizard
        2. Add account
        3. Connect channel
        """
        logger.info("Initializing Telegram bot...")

        # Step 1: Load or create config
        config = self.setup_wizard.load_config()
        if not config:
            logger.info("No existing config, running setup wizard...")
            config = self.setup_wizard.start()
            if not config:
                logger.error("Setup cancelled")
                return False

        # Step 2: Verify account is registered
        account = self.account_manager.resolve_account()
        if not account:
            logger.error("No account available")
            return False

        logger.info(f"✅ Initialized with account: {account.bot_name}")

        # Step 3: Start channel
        await self.channel.start()
        return True

    async def send_example_message(self, target: str) -> None:
        """
        Send example message demonstrating all features
        """
        logger.info(f"Sending example message to {target}")

        # Parse target using targets module
        parsed = self.parser.parse_target(target)
        logger.info(f"Parsed target: {parsed}")

        if not parsed.is_valid:
            logger.error(f"Invalid target: {parsed.error}")
            return

        # Create message
        message = OutgoingMessage(
            target=target,
            text="**Hello from Telegram Bot!** 🎉\n\nThis message demonstrates the complete integration.",
            buttons=[
                [
                    {"text": "✅ Confirm", "callback_data": "confirm"},
                    {"text": "❌ Cancel", "callback_data": "cancel"}
                ]
            ],
            text_mode="markdown",
            silent=False
        )

        # Send via channel (uses accounts + runtime + utils)
        result = await self.channel.send_via_channel(message)

        if result.get("ok"):
            logger.info(f"✅ Message sent: {result['message_id']}")
        else:
            logger.error(f"❌ Failed to send message: {result.get('error')}")

    async def _handle_text_message(self, message) -> None:
        """Handle incoming text message"""
        logger.info(f"Handling text message from {message.user_id}: {message.text}")

        # Example: Echo message
        response = OutgoingMessage(
            target=str(message.chat_id),
            text=f"Echo: {message.text}",
            reply_to=message.message_id
        )

        await self.channel.send_via_channel(response)

    async def _handle_callback(self, message) -> None:
        """Handle button callback"""
        logger.info(f"Handling callback: {message.text}")

    async def _handle_error(self, error: Exception, message) -> None:
        """Handle errors"""
        logger.error(f"Error handling message from {message.user_id}: {str(error)}")

    async def shutdown(self) -> None:
        """Shutdown bot"""
        await self.channel.stop()
        logger.info("Bot shutdown complete")

    def print_stats(self) -> None:
        """Print runtime statistics"""
        stats = self.runtime.get_stats()
        print("\n" + "="*60)
        print("  Runtime Statistics")
        print("="*60)
        for key, value in stats.items():
            print(f"{key:.<40} {value}")
        print("="*60 + "\n")

    def list_accounts(self) -> None:
        """List all accounts"""
        accounts = self.account_manager.list_accounts()

        print("\n" + "="*60)
        print(f"  Available Accounts ({len(accounts)})")
        print("="*60)

        for account in accounts:
            status = "🟢 Active" if account.is_active else "🔴 Inactive"
            print(f"{status} | {account.id}")
            print(f"  Bot: {account.bot_name} (@{account.bot_username})")
            print(f"  Permissions: {', '.join(account.permissions or [])}")
            print()

        print("="*60 + "\n")


# ============ Usage Examples ============

async def example_1_basic_setup():
    """例1: Basic setup and initialization"""
    print("\n" + "🟢 "*20)
    print("  Example 1: Basic Setup and Initialization")
    print("🟢 "*20 + "\n")

    bot = TelegramBotIntegration()

    # Initialize
    if await bot.initialize():
        print("✅ Bot initialized successfully")
        bot.list_accounts()
        await bot.shutdown()
    else:
        print("❌ Failed to initialize bot")


async def example_2_account_management():
    """例2: Account management"""
    print("\n" + "🟢 "*20)
    print("  Example 2: Account Management")
    print("🟢 "*20 + "\n")

    manager = get_account_manager()

    # List accounts
    print("1. Listing accounts:")
    for account in manager.list_accounts():
        print(f"  - {account.id}: {account.bot_name}")

    print("\n✅ Account management example complete")


async def example_3_target_parsing():
    """例3: Target parsing and normalization"""
    print("\n" + "🟢 "*20)
    print("  Example 3: Target Parsing and Normalization")
    print("🟢 "*20 + "\n")

    parser = get_parser()

    # Test different target formats
    test_targets = [
        "123456789",  # Numeric ID
        "@username",  # Username
        "group:123456789",  # Prefixed
        "123456789/thread:456",  # With thread
    ]

    for target in test_targets:
        parsed = parser.parse_target(target)
        print(f"✅ {target:.<40} -> {parsed}")

    print("\n✅ Target parsing example complete")


async def example_4_runtime_context():
    """例4: Runtime context and caching"""
    print("\n" + "🟢 "*20)
    print("  Example 4: Runtime Context and Caching")
    print("🟢 "*20 + "\n")

    context = get_runtime_context()

    # Test caching
    print("1. Testing cache:")
    context.set_cache("test_key", "test_value")
    cached = context.get_cache("test_key")
    print(f"  Cached value: {cached}")

    # Test rate limiting
    print("\n2. Testing rate limiting:")
    for i in range(3):
        delay = context.wait_for_rate_limit()
        print(f"  Request {i+1}: delay={delay:.2f}s")

    # Print stats
    context.reset_stats()
    print("\n✅ Runtime context example complete")


async def example_5_utilities():
    """例5: Utility functions"""
    print("\n" + "🟢 "*20)
    print("  Example 5: Utility Functions")
    print("🟢 "*20 + "\n")

    # Validate chat IDs
    print("1. Validating chat IDs:")
    chat_ids = ["123456789", "-123456789", "@username", "invalid"]
    for chat_id in chat_ids:
        is_valid = validate_chat_id(chat_id)
        is_private = is_private_chat(chat_id)
        print(f"  {chat_id:.<30} valid={is_valid}, private={is_private}")

    print("\n✅ Utilities example complete")


async def example_6_channel_integration():
    """例6: Channel integration and message routing"""
    print("\n" + "🟢 "*20)
    print("  Example 6: Channel Integration")
    print("🟢 "*20 + "\n")

    bot = TelegramBotIntegration()

    if await bot.initialize():
        print("✅ Channel initialized")

        # Example: Send message
        # await bot.send_example_message("123456789")

        bot.print_stats()
        await bot.shutdown()


# ============ Main ============

async def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("  Telegram Bot Integration Examples")
    print("="*60)

    try:
        # Uncomment to run specific examples
        # await example_1_basic_setup()
        # await example_2_account_management()
        await example_3_target_parsing()
        await example_4_runtime_context()
        await example_5_utilities()
        # await example_6_channel_integration()

        print("\n✅ All examples completed!")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
