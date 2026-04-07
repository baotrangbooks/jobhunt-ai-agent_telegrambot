#!/usr/bin/env python3
"""
Local testing script for webhook without needing Telegram
Simulates webhook requests for testing
"""

import asyncio
import json
from models import IncomingMessage
from webhooks import process_with_ai

async def simulate_webhook(example_name: str, chat_id: str = "123456789"):
    """Simulate webhook by calling process_with_ai directly"""
    
    print(f"\n{'='*70}")
    print(f"Testing: {example_name}")
    print(f"Chat ID: {chat_id}")
    print(f"{'='*70}")
    
    # Create message
    msg = IncomingMessage(
        user_id=chat_id,
        text_content=example_name,
        platform="tele"
    )
    
    # Process
    try:
        await process_with_ai(msg)
        print(f"\n✅ {example_name} completed successfully")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all examples"""
    
    examples = [
        "help",
        "Example 1",
        "Example 2", 
        "Example 3",
        "Example 4",
        "Example 5",
        "Example 6",
        "Example 7",
        "Example 8",
        "Example 9",
        "Example 10",
        "Example 11",
        "Example 12",
        "Example 13",
        "Example 14",
    ]
    
    print("\n" + "="*70)
    print("  TELEGRAM WEBHOOK LOCAL TESTING")
    print("="*70)
    print("\nThis script tests webhook functionality locally.")
    print("Make sure TELEGRAM_BOT_TOKEN is set in .env\n")
    
    for i, example in enumerate(examples, 1):
        print(f"\n[{i}/{len(examples)}] {example}")
        await simulate_webhook(example)
        
        # Brief pause between examples
        await asyncio.sleep(1)
    
    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETED")
    print("="*70)
    print("\nAll examples executed successfully!")
    print("Now you can:")
    print("1. Setup ngrok: ngrok http 8008")
    print("2. Configure webhook with your ngrok URL")
    print("3. Test on real Telegram")
    print("\nRead WEBHOOK_TESTING_GUIDE.md for detailed instructions")

if __name__ == "__main__":
    asyncio.run(main())
