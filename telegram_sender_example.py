"""
Example usage of TelegramSender class
Demonstrates all available methods
"""

import asyncio
import os
from dotenv import load_dotenv
from telegram_sender import TelegramSender, RetryConfig, SendOptions

# Load environment variables
load_dotenv()

async def main():
    # Initialize TelegramSender with bot token from env
    sender = TelegramSender()
    
    # Example values (replace with actual values)
    chat_id = "YOUR_CHAT_ID"  # Can be username @username or numeric ID
    message_id = 123  # numeric message ID
    forum_chat_id = "YOUR_FORUM_CHAT_ID"  # Supergroup with forums
    
    try:
        # ===== Example 1: Send a simple message =====
        print("1. Sending simple text message...")
        result = await sender.send_message(
            to=chat_id,
            text="Hello! This is a test message.",
            silent=False,
            text_mode="markdown"
        )
        print(f"Result: {result}")
        if result.get("ok"):
            message_id = result["message_id"]  # Save for other examples
        
        # ===== Example 2: Send message with retry config =====
        print("\n2. Sending message with retry config...")
        retry_config = RetryConfig(max_attempts=5, backoff=1.5, initial_delay=0.3)
        result = await sender.send_message(
            to=chat_id,
            text="Message with retry configuration",
            retry=retry_config
        )
        print(f"Result: {result}")
        
        # ===== Example 3: Send message with inline buttons =====
        print("\n3. Sending message with inline buttons...")
        buttons = [
            [
                {"text": "Python", "callback_data": "lang_python"},
                {"text": "JavaScript", "callback_data": "lang_js"}
            ],
            [
                {"text": "Go", "callback_data": "lang_go"},
                {"text": "Rust", "callback_data": "lang_rust"}
            ]
        ]
        result = await sender.send_message(
            to=chat_id,
            text="Choose your favorite programming language:",
            buttons=buttons
        )
        print(f"Result: {result}")
        
        # ===== Example 4: Send HTML formatted message =====
        print("\n4. Sending HTML formatted message...")
        html_text = """
        <b>Bold text</b>
        <i>Italic text</i>
        <code>code</code>
        <a href="https://example.com">Link</a>
        """
        result = await sender.send_message(
            to=chat_id,
            text=html_text,
            text_mode="html"
        )
        print(f"Result: {result}")
        
        # ===== Example 5: Send typing indicator =====
        print("\n5. Sending typing indicator...")
        result = await sender.send_typing(to=chat_id)
        print(f"Result: {result}")
        
        # Wait a bit before sending actual message
        await asyncio.sleep(2)
        
        # ===== Example 6: Send sticker =====
        print("\n6. Sending sticker...")
        # Sticker file_id from Telegram (you need to get one first)
        sticker_file_id = "CAACAgIAAxkBAAEE..."  # Example sticker ID
        # result = await sender.send_sticker(to=chat_id, file_id=sticker_file_id)
        print("(Skipped - requires valid sticker file_id)")
        
        # ===== Example 7: Send poll =====
        print("\n7. Sending poll...")
        poll_data = {
            "question": "What's your favorite Python version?",
            "options": ["3.8", "3.9", "3.10", "3.11", "3.12"],
            "poll_type": "regular",
            "is_anonymous": True,
            "allows_multiple_answers": False
        }
        result = await sender.send_poll(to=chat_id, poll_data=poll_data)
        print(f"Result: {result}")
        
        # ===== Example 8: Send message with reply_to =====
        print("\n8. Sending reply message...")
        if result.get("ok") and result.get("message_id"):
            result = await sender.send_message(
                to=chat_id,
                text="This is a reply to the previous message",
                reply_to=int(result["message_id"])
            )
            print(f"Result: {result}")
        
        # ===== Example 9: React to message =====
        print("\n9. Adding reaction to message...")
        if message_id:
            result = await sender.react_message(
                chat_id=chat_id,
                message_id=message_id,
                emoji="👍"
            )
            print(f"Result: {result}")
        
        # ===== Example 10: Edit message =====
        print("\n10. Editing message...")
        # Send a message first to edit it
        send_result = await sender.send_message(
            to=chat_id,
            text="Original message"
        )
        if send_result.get("ok"):
            edit_result = await sender.edit_message(
                chat_id=chat_id,
                message_id=send_result["message_id"],
                text="**Edited message** with updated content!"
            )
            print(f"Result: {edit_result}")
        
        # ===== Example 11: Pin message =====
        print("\n11. Pinning message...")
        if send_result.get("ok"):
            pin_result = await sender.pin_message(
                chat_id=chat_id,
                message_id=send_result["message_id"]
            )
            print(f"Result: {pin_result}")
        
        # ===== Example 12: Delete message =====
        print("\n12. Deleting message...")
        # Send a message to delete
        delete_test = await sender.send_message(
            to=chat_id,
            text="This message will be deleted"
        )
        if delete_test.get("ok"):
            delete_result = await sender.delete_message(
                chat_id=chat_id,
                message_id=delete_test["message_id"]
            )
            print(f"Result: {delete_result}")
        
        # ===== Example 13: Create forum topic =====
        print("\n13. Creating forum topic...")
        # This requires a supergroup with forums enabled
        # forum_result = await sender.create_forum_topic(
        #     chat_id=forum_chat_id,
        #     name="General Discussion"
        # )
        print("(Skipped - requires forum-enabled supergroup)")
        
        # ===== Example 14: Send message to forum topic =====
        print("\n14. Sending message to forum topic...")
        # topic_result = await sender.send_message(
        #     to=forum_chat_id,
        #     text="Message in forum topic",
        #     thread_id=123  # Topic/thread ID
        # )
        print("(Skipped - requires forum chat and topic ID)")
        
        # ===== Example 15: Send message with silent flag =====
        print("\n15. Sending silent message (no notification)...")
        result = await sender.send_message(
            to=chat_id,
            text="Silent message - no notification",
            silent=True
        )
        print(f"Result: {result}")
        
        print("\n✅ All examples completed!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        sender.close()

if __name__ == "__main__":
    asyncio.run(main())
