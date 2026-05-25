"""
AI Agent Integration Module
Tích hợp Telegram bot với AI chatbot agent
"""

import sqlite3
import asyncio
import logging
from pathlib import Path
from uuid import uuid4
from typing import AsyncGenerator

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Ensure AI agent assistant is in path
import os
import sys

project_root = Path(__file__).resolve().parent
load_dotenv(dotenv_path=project_root / ".env", override=False)
logger = logging.getLogger(__name__)

ai_agent_path_env = os.getenv("AI_AGENT_ASSISTANT_PATH")
if ai_agent_path_env:
    ai_agent_path = Path(ai_agent_path_env).expanduser().resolve()
    if ai_agent_path.is_file():
        ai_agent_path = ai_agent_path.parent
    if ai_agent_path.name == "ai_agent_assistant":
        ai_agent_path = ai_agent_path.parent
else:
    ai_agent_path = Path(__file__).resolve().parent.parent / "ai-agent-assistant"

if ai_agent_path.exists():
    if str(ai_agent_path) not in sys.path:
        sys.path.insert(0, str(ai_agent_path))
    logger.info(f"Using ai-agent-assistant path: {ai_agent_path}")
else:
    logger.warning(
        f"ai-agent-assistant directory not found at {ai_agent_path}. "
        "Set AI_AGENT_ASSISTANT_PATH to the correct path or install the package in the environment."
    )

# Compatibility shim: some versions of ai-agent-assistant import `UTC` from
# the stdlib `datetime` module (Python 3.11+). On older Python (<3.11)
# `from datetime import UTC` raises ImportError. Provide a fallback so the
# package can import when running on older Python versions (temporary).
try:
    from datetime import UTC  # type: ignore
except Exception:
    import datetime as _dt
    if not hasattr(_dt, "UTC"):
        # Use timezone.utc as equivalent
        _dt.UTC = _dt.timezone.utc

try:
    from ai_agent_assistant import build_local_runtime, stream_chat_turn  # type: ignore[import]
except ImportError as e:
    logger.warning(f"Could not import ai_agent_assistant: {e}")
    build_local_runtime = None
    stream_chat_turn = None


class AIAgentIntegration:
    """Manages integration between Telegram bot and AI chatbot agent."""

    def __init__(self, db_path: str = "ai_memory.db"):
        """
        Initialize AI agent integration.
        
        Args:
            db_path: Path to SQLite database for conversation memory
        """
        self.db_path = db_path
        self.app = None
        self.llm = None
        self.conversation_memory = {}  # Store conversation context by user_id
        self._initialized = False

    async def initialize(self) -> bool:
        """
        Initialize the AI agent runtime.
        
        Returns:
            bool: True if initialized successfully, False otherwise
        """
        try:
            if build_local_runtime is None:
                logger.error("AI agent assistant not available")
                return False

            # Initialize LLM
            self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
            
            # Create or connect to database
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            
            # Build runtime
            self.app = build_local_runtime(self.llm, conn)
            self._initialized = True
            
            logger.info("AI agent integration initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AI agent: {e}")
            return False

    def _get_conversation_history(self, user_id: int) -> list:
        """
        Get conversation history for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            list: List of (role, content) tuples for conversation history
        """
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = []
        return self.conversation_memory[user_id]

    async def chat(self, user_id: int, user_message: str) -> AsyncGenerator[str, None]:
        """
        Send message to AI agent and stream response.
        
        Args:
            user_id: Telegram user ID
            user_message: Message from user
            
        Yields:
            str: Streamed response chunks from AI agent
        """
        if not self._initialized:
            logger.error("AI agent not initialized")
            yield "❌ AI agent is not initialized. Please try again later."
            return

        try:
            # Get conversation history
            history = self._get_conversation_history(user_id)
            
            # Add user message to history
            history.append(("user", user_message))
            
            # Prepare messages for LangChain format
            messages_for_agent = []
            for role, content in history:
                messages_for_agent.append((role, content))
            
            logger.info(f"[User {user_id}] Sending to AI agent: {user_message}")
            
            # Stream response from agent
            full_response = ""
            conversation_id = f"tg_{user_id}"
            
            try:
                stream_gen = stream_chat_turn(
                    app=self.app,
                    messages=messages_for_agent,
                    conversation_id=conversation_id,
                    run_id=uuid4().hex[:12],
                    turn_context={"user_id": user_id},
                    stream_mode="updates",
                    recursion_limit=20,
                )
                
                # Process streamed chunks
                for chunk in stream_gen:
                    if isinstance(chunk, dict):
                        # Extract messages from various node outputs
                        for node_name, output in chunk.items():
                            if "messages" in output and output["messages"]:
                                last_msg = output["messages"][-1]
                                if hasattr(last_msg, "content") and last_msg.content:
                                    content = last_msg.content
                                    if content and content not in full_response:
                                        full_response = content
                                        yield content
                
            except Exception as stream_error:
                logger.error(f"Stream error for user {user_id}: {stream_error}")
                yield f"⚠️ Error during streaming: {str(stream_error)}"
                return
            
            # Add assistant response to history
            if full_response:
                history.append(("assistant", full_response))
            else:
                # If no response extracted, try fallback
                yield "⚠️ No response generated from AI agent."
            
            logger.info(f"[User {user_id}] AI response completed")
            
        except Exception as e:
            logger.error(f"Error in chat with user {user_id}: {e}")
            yield f"❌ Error from AI agent: {str(e)}"

    async def get_response(self, user_id: int, user_message: str, timeout: int = 30) -> str:
        """
        Get complete response from AI agent (non-streaming).
        
        Args:
            user_id: Telegram user ID
            user_message: Message from user
            timeout: Max seconds to wait for response
            
        Returns:
            str: Complete response from AI agent
        """
        try:
            response_parts = []
            
            # Collect all streamed parts
            async for chunk in self.chat(user_id, user_message):
                response_parts.append(chunk)
            
            return "".join(response_parts) if response_parts else "⚠️ No response from AI agent"
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout getting response for user {user_id}")
            return "❌ Request timed out. Please try again."
        except Exception as e:
            logger.error(f"Error getting response for user {user_id}: {e}")
            return f"❌ Error: {str(e)}"

    def clear_conversation(self, user_id: int) -> bool:
        """
        Clear conversation history for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            bool: Success status
        """
        try:
            if user_id in self.conversation_memory:
                self.conversation_memory[user_id] = []
                logger.info(f"Cleared conversation for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing conversation for user {user_id}: {e}")
            return False

    def get_conversation_stats(self, user_id: int) -> dict:
        """
        Get statistics for a user's conversation.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            dict: Conversation statistics
        """
        history = self._get_conversation_history(user_id)
        return {
            "user_id": user_id,
            "total_messages": len(history),
            "user_messages": sum(1 for role, _ in history if role == "user"),
            "assistant_messages": sum(1 for role, _ in history if role == "assistant"),
        }


# Global AI integration instance
_ai_integration = None


async def get_ai_integration(db_path: str = "ai_memory.db") -> AIAgentIntegration:
    """
    Get or create global AI integration instance.
    
    Args:
        db_path: Path to SQLite database for conversation memory
        
    Returns:
        AIAgentIntegration: Global AI integration instance
    """
    global _ai_integration
    
    if _ai_integration is None:
        _ai_integration = AIAgentIntegration(db_path=db_path)
        await _ai_integration.initialize()
    
    return _ai_integration


async def chat_with_ai(user_id: int, message: str) -> AsyncGenerator[str, None]:
    """
    Convenience function to chat with AI agent.
    
    Args:
        user_id: Telegram user ID
        message: User message
        
    Yields:
        str: Response chunks
    """
    integration = await get_ai_integration()
    async for chunk in integration.chat(user_id, message):
        yield chunk


async def get_ai_response(user_id: int, message: str, timeout: int = 30) -> str:
    """
    Convenience function to get complete response from AI agent.
    
    Args:
        user_id: Telegram user ID
        message: User message
        timeout: Max seconds to wait
        
    Returns:
        str: Complete response
    """
    integration = await get_ai_integration()
    return await integration.get_response(user_id, message, timeout=timeout)
