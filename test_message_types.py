#!/usr/bin/env python3
"""
Test script for different message types in webhook
"""

import asyncio
import json
from models import IncomingMessage
from webhooks import process_with_ai

async def test_message_types():
    """Test different message types"""

    test_cases = [
        {
            "name": "Regular text message",
            "message": IncomingMessage(
                user_id="123456789",
                text_content="Hello world",
                platform="tele",
                message_type="text"
            )
        },
        {
            "name": "Callback query (button click)",
            "message": IncomingMessage(
                user_id="123456789",
                text_content="lang_python",
                platform="tele",
                message_type="callback_query"
            )
        },
        {
            "name": "Sticker message",
            "message": IncomingMessage(
                user_id="123456789",
                text_content="[Sticker: 😊]",
                platform="tele",
                message_type="sticker"
            )
        },
        {
            "name": "Photo message",
            "message": IncomingMessage(
                user_id="123456789",
                text_content="[Photo]",
                platform="tele",
                message_type="photo"
            )
        },
        {
            "name": "Edited message",
            "message": IncomingMessage(
                user_id="123456789",
                text_content="Edited text",
                platform="tele",
                message_type="edited_text"
            )
        }
    ]

    print("Testing different message types...")
    print("=" * 50)

    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        print(f"Message: {test_case['message']}")

        try:
            await process_with_ai(test_case['message'])
            print("✅ Processed successfully")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

        print("-" * 30)

    print("\nAll message types tested!")

if __name__ == "__main__":
    asyncio.run(test_message_types())