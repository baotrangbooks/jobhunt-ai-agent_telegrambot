"""
Telegram Account Manager
Quản lý tài khoản bot, xác thực, và quản lý quyền truy cập (Tương tự accounts.ts)
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from pathlib import Path
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class TelegramAccount:
    """Telegram account configuration"""
    id: str
    token: str
    bot_name: Optional[str] = None
    bot_username: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None
    last_validated: Optional[str] = None
    permissions: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Don't expose token in dict
        data['token'] = '***' if data['token'] else None
        return data


class TelegramAccountManager:
    """Manage multiple Telegram bot accounts and authentication"""

    def __init__(self, config_dir: str = ".config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.accounts_file = self.config_dir / "accounts.json"
        self.accounts: Dict[str, TelegramAccount] = {}
        self.token_cache: Dict[str, bool] = {}  # Cache token validation results
        self.cache_ttl = 3600  # 1 hour
        self._load_accounts()

    def _load_accounts(self):
        """Load accounts from JSON file"""
        if self.accounts_file.exists():
            try:
                with open(self.accounts_file, 'r') as f:
                    data = json.load(f)
                    for account_id, account_data in data.items():
                        self.accounts[account_id] = TelegramAccount(**account_data)
                logger.info(f"Loaded {len(self.accounts)} accounts from {self.accounts_file}")
            except Exception as e:
                logger.error(f"Error loading accounts: {str(e)}")
        else:
            logger.info("No accounts file found, starting with empty accounts")

    def _save_accounts(self):
        """Save accounts to JSON file"""
        try:
            accounts_data = {}
            for account_id, account in self.accounts.items():
                account_dict = asdict(account)
                # Store token as-is for local storage
                accounts_data[account_id] = account_dict

            with open(self.accounts_file, 'w') as f:
                json.dump(accounts_data, f, indent=2)
            logger.info(f"Saved {len(self.accounts)} accounts to {self.accounts_file}")
        except Exception as e:
            logger.error(f"Error saving accounts: {str(e)}")

    def add_account(
        self,
        account_id: str,
        token: str,
        bot_name: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add a new account"""
        try:
            # Validate token before adding
            if not self.validate_token(token):
                logger.error(f"Invalid token for account {account_id}")
                return False

            # Get bot info
            bot_info = self._get_bot_info(token)
            if not bot_info:
                logger.error(f"Could not get bot info for account {account_id}")
                return False

            account = TelegramAccount(
                id=account_id,
                token=token,
                bot_name=bot_name or bot_info.get('first_name'),
                bot_username=bot_info.get('username'),
                is_active=True,
                created_at=datetime.utcnow().isoformat(),
                last_validated=datetime.utcnow().isoformat(),
                permissions=permissions or ['send_message', 'receive_message'],
                metadata=metadata
            )

            self.accounts[account_id] = account
            self._save_accounts()
            logger.info(f"Added account {account_id}: {bot_info.get('first_name')}")
            return True

        except Exception as e:
            logger.error(f"Error adding account: {str(e)}")
            return False

    def get_account(self, account_id: str) -> Optional[TelegramAccount]:
        """Get account by ID"""
        return self.accounts.get(account_id)

    def get_bot_token(self, account_id: str) -> Optional[str]:
        """Get bot token for account"""
        account = self.get_account(account_id)
        if account and account.is_active:
            return account.token
        return None

    def list_accounts(self) -> List[TelegramAccount]:
        """List all active accounts"""
        return [acc for acc in self.accounts.values() if acc.is_active]

    def validate_token(self, token: str) -> bool:
        """
        Validate bot token with Telegram API
        Returns True if token is valid
        """
        try:
            # Check cache first
            cached = self.token_cache.get(token)
            if cached is not None:
                return cached

            # Call getMe to validate token
            response = requests.post(
                f"https://api.telegram.org/bot{token}/getMe",
                timeout=5
            )

            is_valid = response.status_code == 200 and response.json().get('ok')
            self.token_cache[token] = is_valid

            if is_valid:
                logger.info(f"Token validated successfully")
            else:
                logger.warning(f"Token validation failed: {response.json().get('description')}")

            return is_valid

        except Exception as e:
            logger.error(f"Error validating token: {str(e)}")
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

            return None

        except Exception as e:
            logger.error(f"Error getting bot info: {str(e)}")
            return None

    def update_account(
        self,
        account_id: str,
        **kwargs
    ) -> bool:
        """Update account properties"""
        try:
            account = self.get_account(account_id)
            if not account:
                logger.error(f"Account {account_id} not found")
                return False

            # Allow updating specific fields
            allowed_fields = ['token', 'bot_name', 'is_active', 'permissions', 'metadata']
            for field, value in kwargs.items():
                if field in allowed_fields:
                    if field == 'token':
                        # Validate new token
                        if not self.validate_token(value):
                            logger.error("Invalid token")
                            return False
                    setattr(account, field, value)

            account.last_validated = datetime.utcnow().isoformat()
            self._save_accounts()
            logger.info(f"Updated account {account_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating account: {str(e)}")
            return False

    def deactivate_account(self, account_id: str) -> bool:
        """Deactivate an account"""
        try:
            account = self.get_account(account_id)
            if not account:
                return False

            account.is_active = False
            self._save_accounts()
            logger.info(f"Deactivated account {account_id}")
            return True

        except Exception as e:
            logger.error(f"Error deactivating account: {str(e)}")
            return False

    def has_permission(self, account_id: str, permission: str) -> bool:
        """Check if account has permission"""
        account = self.get_account(account_id)
        if not account:
            return False
        return permission in (account.permissions or [])

    def resolve_account(self, account_id: Optional[str] = None) -> Optional[TelegramAccount]:
        """
        Resolve account - fallback to first active account if not specified
        Similar to resolveAccount in accounts.ts
        """
        if account_id:
            return self.get_account(account_id)

        # Fallback to first active account
        active_accounts = self.list_accounts()
        if active_accounts:
            return active_accounts[0]

        return None

    def get_account_for_token(self, token: str) -> Optional[TelegramAccount]:
        """Get account by token"""
        for account in self.accounts.values():
            if account.token == token:
                return account
        return None

    def export_accounts(self) -> Dict[str, Dict[str, Any]]:
        """Export accounts (without sensitive info)"""
        return {
            account_id: account.to_dict()
            for account_id, account in self.accounts.items()
        }


# Global instance
_account_manager: Optional[TelegramAccountManager] = None


def get_account_manager() -> TelegramAccountManager:
    """Get or create global account manager"""
    global _account_manager
    if _account_manager is None:
        _account_manager = TelegramAccountManager()
    return _account_manager
