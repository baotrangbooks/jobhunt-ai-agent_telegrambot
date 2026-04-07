"""
Setup Wizard and Configuration
Cấu hình bot token, policies, và settings (Tương tự setup-core.ts)
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import requests

from accounts import TelegramAccountManager

logger = logging.getLogger(__name__)


@dataclass
class TelegramConfig:
    """Telegram configuration"""
    # Bot settings
    bot_token: str
    bot_name: Optional[str] = None

    # Policies
    allow_pm: bool = True  # Allow private messages
    allow_groups: bool = True
    allow_channels: bool = False

    # Security
    admin_ids: list = None  # Admin user IDs
    blocked_ids: list = None  # Blocked user IDs

    # Advanced
    webhook_url: Optional[str] = None
    polling_enabled: bool = False
    polling_timeout: int = 30

    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None

    def __post_init__(self):
        """Initialize default values"""
        if self.admin_ids is None:
            self.admin_ids = []
        if self.blocked_ids is None:
            self.blocked_ids = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "bot_token": "***" if self.bot_token else None,  # Don't expose
            "bot_name": self.bot_name,
            "allow_pm": self.allow_pm,
            "allow_groups": self.allow_groups,
            "allow_channels": self.allow_channels,
            "admin_ids": self.admin_ids or [],
            "blocked_ids": self.blocked_ids or [],
            "webhook_url": self.webhook_url,
            "polling_enabled": self.polling_enabled,
            "polling_timeout": self.polling_timeout,
            "log_level": self.log_level,
            "log_file": self.log_file,
        }


class SetupWizard:
    """
    Interactive setup wizard for Telegram bot configuration
    """

    def __init__(self, config_dir: str = ".config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "telegram_config.json"
        self.account_manager = TelegramAccountManager(config_dir)

    def start(self) -> TelegramConfig:
        """Start interactive setup"""
        print("\n" + "="*60)
        print("  Telegram Bot Configuration Wizard")
        print("="*60 + "\n")

        # Check if config exists
        if self.config_file.exists():
            response = input("Configuration file already exists. Overwrite? (y/n): ").strip().lower()
            if response != 'y':
                return self.load_config()

        # Get bot token
        bot_token = self._prompt_bot_token()
        if not bot_token:
            print("Setup cancelled.")
            return None

        # Get bot info
        bot_info = self._get_bot_info(bot_token)
        if not bot_info:
            print("Failed to validate token. Setup cancelled.")
            return None

        bot_name = bot_info.get('first_name', 'Unknown')
        bot_username = bot_info.get('username', '')

        print(f"\n✅ Bot verified: {bot_name} (@{bot_username})")

        # Get policies
        print("\n" + "-"*60)
        print("Configuration Policies")
        print("-"*60)

        allow_pm = self._prompt_yes_no("Allow private messages?", True)
        allow_groups = self._prompt_yes_no("Allow group messages?", True)
        allow_channels = self._prompt_yes_no("Allow channel messages?", False)

        # Get admin IDs
        admin_ids_str = input("Admin user IDs (comma-separated, or empty): ").strip()
        admin_ids = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip().isdigit()]

        # Get webhook settings
        print("\n" + "-"*60)
        print("Webhook/Polling Configuration")
        print("-"*60)

        use_webhook = self._prompt_yes_no("Use webhook (recommended)", True)
        webhook_url = None
        polling_enabled = False

        if use_webhook:
            webhook_url = input("Webhook URL (e.g., https://example.com/webhook): ").strip()
        else:
            polling_enabled = self._prompt_yes_no("Use polling instead", True)

        # Create config
        config = TelegramConfig(
            bot_token=bot_token,
            bot_name=bot_name,
            allow_pm=allow_pm,
            allow_groups=allow_groups,
            allow_channels=allow_channels,
            admin_ids=admin_ids,
            webhook_url=webhook_url,
            polling_enabled=polling_enabled
        )

        # Save config
        if self.save_config(config):
            print("\n✅ Configuration saved!")

            # Add to account manager
            account_id = bot_username or f"account_{len(self.account_manager.accounts) + 1}"
            self.account_manager.add_account(
                account_id=account_id,
                token=bot_token,
                bot_name=bot_name,
                permissions=['send_message', 'receive_message', 'edit_message', 'delete_message']
            )

            print(f"✅ Account added: {account_id}\n")
            return config
        else:
            print("\n❌ Failed to save configuration")
            return None

    def load_config(self) -> Optional[TelegramConfig]:
        """Load configuration from file"""
        if not self.config_file.exists():
            logger.warning(f"Config file not found: {self.config_file}")
            return None

        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)

            config = TelegramConfig(**data)
            return config
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return None

    def save_config(self, config: TelegramConfig) -> bool:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(asdict(config), f, indent=2)
            logger.info(f"Config saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
            return False

    def _get_bot_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get bot info from Telegram API"""
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{token}/getMe",
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return data.get('result')

            error_msg = data.get('description', 'Unknown error')
            print(f"❌ Error: {error_msg}")
            return None

        except Exception as e:
            print(f"❌ Error connecting to Telegram: {str(e)}")
            return None

    def _validate_token(self, token: str) -> bool:
        """Validate token format"""
        return bool(token and ':' in token and len(token) > 20)

    def _prompt_bot_token(self) -> Optional[str]:
        """Prompt for bot token"""
        while True:
            token = input("Enter your Telegram bot token: ").strip()

            if not token:
                return None

            if not self._validate_token(token):
                print("❌ Invalid token format (should be like 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11)")
                continue

            print("Validating token...")
            if self._get_bot_info(token):
                return token
            else:
                print("❌ Token validation failed. Please check and try again.")

    def _prompt_yes_no(self, prompt: str, default: bool = True) -> bool:
        """Prompt for yes/no answer"""
        default_str = "(Y/n)" if default else "(y/N)"
        response = input(f"{prompt} {default_str}: ").strip().lower()

        if not response:
            return default

        return response in ['y', 'yes']

    def test_connection(self, config: TelegramConfig) -> bool:
        """Test bot connection"""
        print("\nTesting connection...")

        # Test getMe
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{config.bot_token}/getMe",
                timeout=5
            )

            if response.status_code == 200 and response.json().get('ok'):
                bot_info = response.json()['result']
                print(f"✅ Bot connection successful: {bot_info['first_name']}")
                return True
            else:
                print(f"❌ Bot connection failed: {response.json().get('description')}")
                return False

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False

    def test_webhook(self, config: TelegramConfig) -> bool:
        """Test webhook configuration"""
        if not config.webhook_url:
            print("⚠️  No webhook URL configured")
            return False

        print(f"\nTesting webhook: {config.webhook_url}")

        try:
            # Set webhook
            response = requests.post(
                f"https://api.telegram.org/bot{config.bot_token}/setWebhook",
                json={"url": config.webhook_url},
                timeout=10
            )

            if response.status_code == 200 and response.json().get('ok'):
                print(f"✅ Webhook set successfully")
                return True
            else:
                print(f"❌ Webhook failed: {response.json().get('description')}")
                return False

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False


async def auto_setup(config_dir: str = ".config") -> Optional[TelegramConfig]:
    """
    Automatic setup from environment variables
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not set in environment")
        return None

    wizard = SetupWizard(config_dir)

    # Try to load existing config first
    config = wizard.load_config()
    if config and config.bot_token == token:
        logger.info("Using existing configuration from file")
        return config

    # Create new config from env vars
    config = TelegramConfig(
        bot_token=token,
        bot_name=os.getenv("TELEGRAM_BOT_NAME", ""),
        allow_pm=os.getenv("TELEGRAM_ALLOW_PM", "true").lower() == "true",
        allow_groups=os.getenv("TELEGRAM_ALLOW_GROUPS", "true").lower() == "true",
        allow_channels=os.getenv("TELEGRAM_ALLOW_CHANNELS", "false").lower() == "true",
        webhook_url=os.getenv("TELEGRAM_WEBHOOK_URL"),
        polling_enabled=os.getenv("TELEGRAM_POLLING", "false").lower() == "true",
    )

    # Validate
    if wizard.test_connection(config):
        wizard.save_config(config)
        logger.info("Auto-setup completed")
        return config
    else:
        logger.error("Auto-setup failed: invalid token")
        return None


# Utility functions
def get_config_from_file(config_dir: str = ".config") -> Optional[TelegramConfig]:
    """Load config from file"""
    wizard = SetupWizard(config_dir)
    return wizard.load_config()


def create_default_config(bot_token: str) -> TelegramConfig:
    """Create default configuration"""
    return TelegramConfig(
        bot_token=bot_token,
        allow_pm=True,
        allow_groups=True,
        allow_channels=False,
        webhook_url=None,
        polling_enabled=True
    )
