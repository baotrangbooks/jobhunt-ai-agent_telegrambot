"""
Unit tests for TelegramSender class
"""

import pytest
import asyncio
from telegram_sender import TelegramSender, RetryConfig, SendOptions, RateLimiter
import os


# Mock environment
@pytest.fixture
def mock_token():
    """Mock Telegram bot token"""
    return "123456789:ABCdefGhIjKLmnoPqrStUvWxYz"


@pytest.fixture
def sender(mock_token):
    """Create TelegramSender instance with mock token"""
    os.environ["TELEGRAM_BOT_TOKEN"] = mock_token
    return TelegramSender(token=mock_token)


class TestTelegramSender:
    """Test TelegramSender class"""

    def test_initialization(self, sender):
        """Test TelegramSender initialization"""
        assert sender.token is not None
        assert sender.base_url.startswith("https://api.telegram.org/bot")
        assert sender.rate_limiter is not None

    def test_token_resolution(self, mock_token):
        """Test token resolution"""
        sender = TelegramSender(token=mock_token)
        assert sender._resolve_token(mock_token) == mock_token
        assert sender._resolve_token(None) == mock_token

    def test_token_missing(self):
        """Test error when token is missing"""
        with pytest.raises(ValueError, match="not provided"):
            sender = TelegramSender(token=None)
            # Clear env to test
            if "TELEGRAM_BOT_TOKEN" in os.environ:
                del os.environ["TELEGRAM_BOT_TOKEN"]

    @pytest.mark.asyncio
    async def test_chat_id_caching(self, sender):
        """Test chat ID caching"""
        chat_id = "123456789"
        sender.chat_id_cache[chat_id] = "789654321"
        
        # Should return cached value without API call
        cached = sender.chat_id_cache.get(chat_id)
        assert cached == "789654321"

    def test_text_chunking(self, sender):
        """Test text chunking logic"""
        short_text = "Hello"
        chunks = sender._chunk_text(short_text, limit=100)
        assert len(chunks) == 1
        assert chunks[0] == short_text

        long_text = "a" * 10000
        chunks = sender._chunk_text(long_text, limit=4000)
        assert len(chunks) == 3  # 4000 + 4000 + 2000
        assert chunks[0] == "a" * 4000

    def test_empty_text_chunking(self, sender):
        """Test chunking empty text"""
        chunks = sender._chunk_text("", limit=100)
        assert len(chunks) == 0

    def test_inline_keyboard_building(self, sender):
        """Test inline keyboard construction"""
        buttons = [
            [
                {"text": "Button 1", "callback_data": "btn1"},
                {"text": "Button 2", "callback_data": "btn2"}
            ]
        ]
        keyboard = sender._build_inline_keyboard(buttons)
        assert keyboard is not None
        assert "inline_keyboard" in keyboard
        assert len(keyboard["inline_keyboard"]) == 1
        assert len(keyboard["inline_keyboard"][0]) == 2

    def test_empty_inline_keyboard(self, sender):
        """Test building keyboard with no buttons"""
        buttons = None
        keyboard = sender._build_inline_keyboard(buttons)
        assert keyboard is None

    def test_html_text_rendering(self, sender):
        """Test HTML text conversion"""
        markdown_text = "**bold** *italic* `code` [link](https://example.com)"
        html = sender._render_html_text(markdown_text)
        
        assert "<b>bold</b>" in html
        assert "<i>italic</i>" in html
        assert "<code>code</code>" in html
        assert '<a href="https://example.com">link</a>' in html

    def test_rate_limiter(self):
        """Test rate limiter"""
        limiter = RateLimiter(delay=0.01)
        import time
        
        start = time.time()
        limiter.wait()
        limiter.wait()
        elapsed = time.time() - start
        
        # Should have enforced delay between calls
        assert elapsed >= 0.01

    def test_retry_config(self):
        """Test RetryConfig dataclass"""
        retry = RetryConfig(max_attempts=5, backoff=1.5, initial_delay=0.3)
        assert retry.max_attempts == 5
        assert retry.backoff == 1.5
        assert retry.initial_delay == 0.3

    def test_send_options(self):
        """Test SendOptions dataclass"""
        opts = SendOptions(
            token="test",
            timeout=30,
            silent=True,
            text_mode="html"
        )
        assert opts.token == "test"
        assert opts.timeout == 30
        assert opts.silent is True
        assert opts.text_mode == "html"

    def test_context_manager(self, sender):
        """Test context manager interface"""
        with sender as s:
            assert s is not None
            assert s.session is not None


class TestSendOptions:
    """Test SendOptions configuration"""

    def test_default_options(self):
        """Test default SendOptions values"""
        opts = SendOptions()
        assert opts.token is None
        assert opts.timeout == 30
        assert opts.silent is False
        assert opts.text_mode == "markdown"
        assert opts.force_document is False

    def test_custom_options(self):
        """Test custom SendOptions"""
        opts = SendOptions(
            token="custom_token",
            timeout=60,
            silent=True,
            thread_id=123,
            reply_to=456
        )
        assert opts.token == "custom_token"
        assert opts.timeout == 60
        assert opts.silent is True
        assert opts.thread_id == 123
        assert opts.reply_to == 456


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v"])
