"""
Example: Using AI Integration with Telegram Bot
Các ví dụ cách sử dụng AI agent integration
"""

import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============ Example 1: Simple Chat ============

async def example_1_simple_chat():
    """Ví dụ 1: Chat đơn giản với AI agent"""
    logger.info("\n" + "=" * 60)
    logger.info("Example 1: Simple Chat with AI Agent")
    logger.info("=" * 60)
    
    from ai_integration import get_ai_integration
    
    ai = await get_ai_integration()
    
    user_id = 123456789
    user_message = "What is machine learning?"
    
    logger.info(f"\nUser: {user_message}")
    logger.info("Waiting for AI response...")
    
    response = await ai.get_response(user_id, user_message)
    logger.info(f"\nAssistant: {response[:200]}...")
    
    return response


# ============ Example 2: Multi-turn Conversation ============

async def example_2_multi_turn():
    """Ví dụ 2: Cuộc trò chuyện multi-turn (ghi nhớ context)"""
    logger.info("\n" + "=" * 60)
    logger.info("Example 2: Multi-turn Conversation with Context")
    logger.info("=" * 60)
    
    from ai_integration import get_ai_integration
    
    ai = await get_ai_integration()
    user_id = 987654321
    
    # First message
    logger.info("\n[Turn 1]")
    msg1 = "My name is Alice and I love Python"
    logger.info(f"User: {msg1}")
    
    response1 = await ai.get_response(user_id, msg1)
    logger.info(f"Assistant: {response1[:150]}...")
    
    # Second message (should remember Alice and Python)
    await asyncio.sleep(1)
    logger.info("\n[Turn 2]")
    msg2 = "What programming language do I like?"
    logger.info(f"User: {msg2}")
    
    response2 = await ai.get_response(user_id, msg2)
    logger.info(f"Assistant: {response2[:150]}...")
    logger.info("\n✅ AI remembered from previous message!")
    
    # Show conversation stats
    stats = ai.get_conversation_stats(user_id)
    logger.info(f"\nConversation Stats:")
    logger.info(f"  Total messages: {stats['total_messages']}")
    logger.info(f"  User messages: {stats['user_messages']}")
    logger.info(f"  Assistant messages: {stats['assistant_messages']}")
    
    return response2


# ============ Example 3: Streaming Responses ============

async def example_3_streaming():
    """Ví dụ 3: Streaming responses (real-time chunks)"""
    logger.info("\n" + "=" * 60)
    logger.info("Example 3: Streaming Responses")
    logger.info("=" * 60)
    
    from ai_integration import get_ai_integration
    
    ai = await get_ai_integration()
    user_id = 555666777
    user_message = "Tell me about artificial intelligence in 3 paragraphs"
    
    logger.info(f"\nUser: {user_message}")
    logger.info("\nStreaming response:")
    
    full_response = ""
    i = 0
    async for chunk in ai.chat(user_id, user_message):
        if chunk:
            full_response += chunk
            i += 1
            if i == 1:
                logger.info(chunk[:100] + "...")
    
    logger.info(f"\n✅ Received {len(full_response)} characters total")
    
    return full_response


# ============ Example 4: Handling Long Responses ============

async def example_4_long_response():
    """Ví dụ 4: Xử lý response dài (auto-split)"""
    logger.info("\n" + "=" * 60)
    logger.info("Example 4: Handling Long Responses (Auto-split)")
    logger.info("=" * 60)
    
    from ai_integration import get_ai_integration
    
    ai = await get_ai_integration()
    user_id = 111222333
    
    # Request a very long response
    user_message = "Write a comprehensive guide on Python programming (make it very detailed)"
    
    logger.info(f"\nUser: {user_message}")
    logger.info("Processing long response...")
    
    response = await ai.get_response(user_id, user_message, timeout=45)
    
    logger.info(f"\n✅ Response length: {len(response)} characters")
    
    # In actual Telegram, this would be auto-split into multiple messages
    if len(response) > 4096:
        num_chunks = (len(response) + 4095) // 4096
        logger.info(f"   In Telegram, this would be sent as {num_chunks} messages")
    else:
        logger.info(f"   Fits in 1 Telegram message")
    
    return response


# ============ Example 5: Error Handling & Timeout ============

async def example_5_error_handling():
    """Ví dụ 5: Xử lý lỗi và timeout"""
    logger.info("\n" + "=" * 60)
    logger.info("Example 5: Error Handling & Timeout")
    logger.info("=" * 60)
    
    from ai_integration import get_ai_integration
    
    ai = await get_ai_integration()
    user_id = 444555666
    
    # Example: short timeout to demonstrate timeout handling
    user_message = "Explain quantum computing in detail"
    
    logger.info(f"\nUser: {user_message}")
    logger.info("Requesting with 10 second timeout...")
    
    try:
        response = await ai.get_response(
            user_id,
            user_message,
            timeout=10
        )
        logger.info(f"✅ Got response: {response[:100]}...")
        
    except asyncio.TimeoutError:
        logger.warning("⏱️ Request timed out (expected for complex queries)")
        logger.info("In production, user would see: 'Response is taking longer...'")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")


# ============ Example 6: Clear Conversation ============

async def example_6_clear_conversation():
    """Ví dụ 6: Xóa lịch sử cuộc trò chuyện"""
    logger.info("\n" + "=" * 60)
    logger.info("Example 6: Clear Conversation")
    logger.info("=" * 60)
    
    from ai_integration import get_ai_integration
    
    ai = await get_ai_integration()
    user_id = 777888999
    
    # Add some messages
    logger.info("\nUser: Hello, my name is Bob")
    await ai.get_response(user_id, "Hello, my name is Bob")
    
    logger.info("User: What's my name?")
    response1 = await ai.get_response(user_id, "What's my name?")
    logger.info(f"Assistant: {response1[:100]}...")
    
    # Show stats before clear
    stats_before = ai.get_conversation_stats(user_id)
    logger.info(f"\nBefore clear: {stats_before['total_messages']} messages")
    
    # Clear conversation
    logger.info("\n🗑️ Clearing conversation...")
    ai.clear_conversation(user_id)
    
    # Show stats after clear
    stats_after = ai.get_conversation_stats(user_id)
    logger.info(f"After clear: {stats_after['total_messages']} messages")
    
    # Try asking again (should not remember)
    logger.info("\nUser: What's my name?")
    response2 = await ai.get_response(user_id, "What's my name?")
    logger.info(f"Assistant: {response2[:150]}...")
    logger.info("\n✅ AI forgot previous context after clear!")


# ============ Example 7: Multiple Users ============

async def example_7_multiple_users():
    """Ví dụ 7: Xử lý multiple users (conversation isolation)"""
    logger.info("\n" + "=" * 60)
    logger.info("Example 7: Multiple Users (Isolated Conversations)")
    logger.info("=" * 60)
    
    from ai_integration import get_ai_integration
    
    ai = await get_ai_integration()
    
    # User 1
    user_id_1 = 100001
    logger.info(f"\n[User 1: {user_id_1}]")
    logger.info("User: My name is Alice")
    await ai.get_response(user_id_1, "My name is Alice")
    
    # User 2
    user_id_2 = 100002
    logger.info(f"\n[User 2: {user_id_2}]")
    logger.info("User: My name is Bob")
    await ai.get_response(user_id_2, "My name is Bob")
    
    # Ask both who they are
    logger.info(f"\n[User 1: {user_id_1}]")
    logger.info("User: Who am I?")
    response1 = await ai.get_response(user_id_1, "Who am I?")
    logger.info(f"Assistant: {response1[:100]}...")
    
    logger.info(f"\n[User 2: {user_id_2}]")
    logger.info("User: Who am I?")
    response2 = await ai.get_response(user_id_2, "Who am I?")
    logger.info(f"Assistant: {response2[:100]}...")
    
    logger.info("\n✅ Each user has separate conversation memory!")


# ============ Example 8: Integration with Telegram ============

async def example_8_telegram_integration():
    """Ví dụ 8: Tích hợp với Telegram bot"""
    logger.info("\n" + "=" * 60)
    logger.info("Example 8: Integration with Telegram Bot")
    logger.info("=" * 60)
    
    from ai_integration import get_ai_integration
    from telegram_sender import TelegramSender
    
    # This is what happens inside process_with_ai() in webhooks.py
    
    logger.info("\n1. Receive message from Telegram")
    user_id = "123456789"
    user_message = "What is the weather like?"
    logger.info(f"   From: {user_id}")
    logger.info(f"   Message: {user_message}")
    
    logger.info("\n2. Call AI agent")
    ai = await get_ai_integration()
    response = await ai.get_response(int(user_id), user_message)
    logger.info(f"   Response: {response[:100]}...")
    
    logger.info("\n3. Send back to Telegram (simulated)")
    logger.info(f"   This would call: TelegramSender.send_message()")
    logger.info(f"   Message length: {len(response)} chars")
    
    if len(response) > 4096:
        logger.info(f"   ⚠️ Message would be split into chunks")
    else:
        logger.info(f"   ✅ Fits in single Telegram message")


# ============ Main Function ============

async def main():
    """Run all examples"""
    logger.info("\n")
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " " * 58 + "║")
    logger.info("║" + "  AI Integration Examples".center(58) + "║")
    logger.info("║" + " " * 58 + "║")
    logger.info("╚" + "=" * 58 + "╝")
    
    try:
        # Check if AI integration works
        from ai_integration import get_ai_integration
        ai = await get_ai_integration()
        if not ai._initialized:
            logger.error("❌ AI integration not initialized!")
            logger.error("   Make sure OPENAI_API_KEY is set in .env")
            return
        
        # Run examples
        examples = [
            ("1", example_1_simple_chat, "Simple Chat"),
            ("2", example_2_multi_turn, "Multi-turn Conversation"),
            ("3", example_3_streaming, "Streaming Responses"),
            ("4", example_4_long_response, "Long Responses"),
            ("5", example_5_error_handling, "Error Handling"),
            ("6", example_6_clear_conversation, "Clear Conversation"),
            ("7", example_7_multiple_users, "Multiple Users"),
            ("8", example_8_telegram_integration, "Telegram Integration"),
        ]
        
        while True:
            logger.info("\n" + "=" * 60)
            logger.info("Available Examples:")
            for num, _, desc in examples:
                logger.info(f"  {num} - {desc}")
            logger.info("  0 - Run all")
            logger.info("  q - Quit")
            logger.info("=" * 60)
            
            choice = input("\nChoose example (0-8, q): ").strip().lower()
            
            if choice == "q":
                logger.info("Goodbye!")
                break
            elif choice == "0":
                logger.info("\nRunning all examples...\n")
                for num, func, _ in examples:
                    try:
                        await func()
                    except Exception as e:
                        logger.error(f"Error in example {num}: {e}")
                    await asyncio.sleep(0.5)
                break
            
            elif choice in [x[0] for x in examples]:
                for num, func, _ in examples:
                    if num == choice:
                        try:
                            await func()
                        except Exception as e:
                            logger.error(f"Error: {e}")
                            import traceback
                            traceback.print_exc()
                        break
            else:
                logger.error("Invalid choice!")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n\nCancelled by user")
