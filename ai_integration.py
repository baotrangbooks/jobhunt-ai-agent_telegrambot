"""
AI Agent Integration Module
Tích hợp Telegram bot với AI chatbot agent
"""

import patch_datetime  # type: ignore

import inspect
import sqlite3
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
from typing import AsyncGenerator, Callable, Optional, List, Dict, Any, Tuple, Union

from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent
load_dotenv(dotenv_path=project_root / ".env", override=False)
backend_env_path = project_root.parent / "FastAPI-boilerplate" / "src" / ".env"
if backend_env_path.exists():
    load_dotenv(dotenv_path=backend_env_path, override=False)
logger = logging.getLogger(__name__)

AI_AGENT_ENV_VARS = ["AI_AGENT_ASSISTANT_PATH", "AI_ASSISTANT_PATH"]


def _resolve_ai_agent_path() -> Path:
    for env_var in AI_AGENT_ENV_VARS:
        env_path = os.getenv(env_var)
        if env_path:
            candidate = Path(env_path).expanduser().resolve()
            if candidate.is_file():
                candidate = candidate.parent
            if candidate.name == "ai_agent_assistant":
                candidate = candidate.parent
            if (candidate / "ai_agent_assistant" / "__init__.py").exists():
                return candidate
            logger.warning(f"Ignoring invalid {env_var}: {candidate}")

    workspace_candidate = Path(__file__).resolve().parent.parent / "ai-agent-assistant"
    if (workspace_candidate / "ai_agent_assistant" / "__init__.py").exists():
        return workspace_candidate
    return workspace_candidate


def _ensure_ai_agent_in_path() -> None:
    ai_agent_path = _resolve_ai_agent_path()
    if ai_agent_path.exists():
        if str(ai_agent_path) not in sys.path:
            sys.path.insert(0, str(ai_agent_path))
        logger.info(f"Using ai-agent-assistant path: {ai_agent_path}")
    else:
        logger.warning(
            f"ai-agent-assistant directory not found at {ai_agent_path}. "
            "Set AI_AGENT_ASSISTANT_PATH or AI_ASSISTANT_PATH to the correct path or install the package in the environment."
        )


_ensure_ai_agent_in_path()

build_chat_app = None
build_local_runtime = None
build_runtime = None
stream_chat_turn = None
run_chat_turn = None
configure_job_search_provider_fn = None

try:
    import ai_agent_assistant as ai_agent_assistant  # type: ignore[import]
    build_chat_app = getattr(ai_agent_assistant, "build_chat_app", None)
    build_local_runtime = getattr(ai_agent_assistant, "build_local_runtime", None)
    build_runtime = getattr(ai_agent_assistant, "build_runtime", None)
    stream_chat_turn = getattr(ai_agent_assistant, "stream_chat_turn", None)
    run_chat_turn = getattr(ai_agent_assistant, "run_chat_turn", None)
    configure_job_search_provider_fn = getattr(ai_agent_assistant, "configure_job_search_provider", None)
except ImportError as e:
    logger.warning(f"Could not import ai_agent_assistant: {e}")
except Exception as e:
    logger.warning(f"Unexpected error importing ai_agent_assistant: {e}")


def _build_runtime_app(llm: Any, conn: sqlite3.Connection) -> Any:
    candidates = [
        ("build_chat_app", build_chat_app),
        ("build_local_runtime", build_local_runtime),
        ("build_runtime", build_runtime),
    ]

    for name, builder in candidates:
        if builder is None:
            continue
        try:
            signature = inspect.signature(builder)
            params = signature.parameters
            if len(params) == 0:
                return builder()
            if "llm" in params and "conn" in params:
                return builder(llm, conn)
            if "llm" in params:
                return builder(llm)
            if "conn" in params:
                return builder(conn)
            return builder()
        except Exception as exc:
            logger.warning(f"Runtime builder {name} failed: {exc}")
    raise RuntimeError("No available AI runtime builder found in ai_agent_assistant.")


def _normalize_message(message: Union[Dict[str, str], Tuple[str, str], List[Any]]) -> Dict[str, str]:
    if isinstance(message, dict):
        return {"role": str(message.get("role", "user")), "content": str(message.get("content", ""))}
    if isinstance(message, (list, tuple)) and len(message) == 2:
        return {"role": str(message[0]), "content": str(message[1])}
    raise TypeError("Messages must be tuple/list pairs or dicts with role/content")


def _normalize_messages(messages: List[Union[Dict[str, str], Tuple[str, str]]]) -> List[Dict[str, str]]:
    return [_normalize_message(item) for item in messages]


def _extract_assistant_content_from_output(output: Any) -> Optional[str]:
    if output is None:
        return None
    if isinstance(output, str):
        return output.strip()
    if isinstance(output, dict):
        if "content" in output and isinstance(output["content"], str):
            return output["content"].strip()
        if "messages" in output and isinstance(output["messages"], list):
            for item in reversed(output["messages"]):
                content = _extract_assistant_content_from_output(item)
                if content:
                    return content
        for value in output.values():
            content = _extract_assistant_content_from_output(value)
            if content:
                return content
        return None
    if isinstance(output, (list, tuple)):
        for item in reversed(output):
            content = _extract_assistant_content_from_output(item)
            if content:
                return content
        return None
    if hasattr(output, "content"):
        content = getattr(output, "content")
        if isinstance(content, str):
            return content.strip()
    return None


def _extract_assistant_content_from_result(result: Any) -> Optional[str]:
    if isinstance(result, dict):
        extracted = _extract_assistant_content_from_output(result.get("final_state", result))
        if extracted:
            return extracted
        if "chunks" in result and isinstance(result["chunks"], list):
            return _extract_assistant_content_from_output(result["chunks"])
    return _extract_assistant_content_from_output(result)


def _build_turn_context(user_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    context: Dict[str, Any] = {"user_id": user_id}
    if metadata:
        context.update(metadata)
    if "user_profile" not in context:
        context["user_profile"] = {"channel": "telegram", "telegram_chat_id": user_id}
    return context


def configure_job_search_provider(provider: Callable[..., Any]) -> None:
    if configure_job_search_provider_fn is None:
        raise RuntimeError("configure_job_search_provider is not available in ai_agent_assistant")
    configure_job_search_provider_fn(provider)


def _configure_default_job_search_provider() -> None:
    if configure_job_search_provider_fn is None:
        logger.warning("configure_job_search_provider is not available in ai_agent_assistant")
        return
    try:
        from job_search_provider import search_jobs_from_supabase_catalog

        configure_job_search_provider_fn(search_jobs_from_supabase_catalog)
        logger.info("Configured Telegram bot job search provider with Supabase catalog")
    except Exception as exc:
        logger.error(f"Failed to configure Telegram job search provider: {exc}")


class AIAgentIntegration:
    """Manages integration between Telegram bot and AI chatbot agent."""

    def __init__(self, db_path: str = "ai_memory.db"):
        self.db_path = db_path
        self.app = None
        self.llm = None
        self.conn: Optional[sqlite3.Connection] = None
        self._initialized = False

    async def initialize(self) -> bool:
        try:
            if build_chat_app is None and build_local_runtime is None and build_runtime is None:
                logger.error("AI agent runtime builder not available")
                return False

            _configure_default_job_search_provider()

            from langchain_openai import ChatOpenAI

            model = os.getenv("AI_ASSISTANT_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
            temperature = float(os.getenv("AI_ASSISTANT_TEMPERATURE", "0"))
            self.llm = ChatOpenAI(model=model, temperature=temperature)
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self._initialize_database()

            app_candidate = _build_runtime_app(self.llm, self.conn)
            if inspect.isawaitable(app_candidate):
                self.app = await app_candidate
            else:
                self.app = app_candidate

            self._initialized = True
            logger.info("AI agent integration initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize AI agent: {e}")
            return False

    def _initialize_database(self) -> None:
        if self.conn is None:
            raise RuntimeError("Database connection is not initialized")
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS telegram_users (
                telegram_chat_id TEXT PRIMARY KEY,
                internal_user_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS telegram_conversations (
                conversation_id TEXT PRIMARY KEY,
                telegram_chat_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS telegram_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                message_type TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bot_link_reminders (
                channel TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                last_sent_at TEXT NOT NULL,
                PRIMARY KEY (channel, chat_id)
            )
            """
        )
        self.conn.commit()

    def ensure_telegram_user(self, telegram_chat_id: str, internal_user_id: Optional[str] = None) -> Optional[str]:
        """Ensure Telegram user exists in database. Return the internal_user_id."""
        if self.conn is None:
            raise RuntimeError("Database connection is not initialized")
        if internal_user_id is None:
            internal_user_id = f"telegram_{telegram_chat_id}"
        self.conn.execute(
            "INSERT OR IGNORE INTO telegram_users (telegram_chat_id, internal_user_id) VALUES (?, ?)",
            (telegram_chat_id, internal_user_id),
        )
        self.conn.commit()
        return internal_user_id
    
    def get_telegram_user(self, telegram_chat_id: str) -> Optional[Dict[str, str]]:
        """Get Telegram user mapping from database."""
        if self.conn is None:
            raise RuntimeError("Database connection is not initialized")
        cursor = self.conn.execute(
            "SELECT telegram_chat_id, internal_user_id FROM telegram_users WHERE telegram_chat_id = ?",
            (telegram_chat_id,),
        )
        row = cursor.fetchone()
        if row:
            return {"telegram_chat_id": row["telegram_chat_id"], "internal_user_id": row["internal_user_id"]}
        return None

    def list_known_chat_ids(self) -> Dict[str, List[str]]:
        """Return known Telegram/Zalo chat IDs that have interacted with the bot."""
        if self.conn is None:
            raise RuntimeError("Database connection is not initialized")
        cursor = self.conn.execute("SELECT telegram_chat_id FROM telegram_users ORDER BY created_at ASC")
        telegram_ids: List[str] = []
        zalo_ids: List[str] = []
        for row in cursor.fetchall():
            chat_id = str(row["telegram_chat_id"] or "").strip()
            if not chat_id:
                continue
            if chat_id.startswith("zalo:"):
                zalo_ids.append(chat_id.removeprefix("zalo:"))
            else:
                telegram_ids.append(chat_id)
        return {"telegram": telegram_ids, "zalo": zalo_ids}

    def should_send_bot_link_reminder(self, *, channel: str, chat_id: str, cooldown_seconds: int) -> bool:
        if self.conn is None:
            raise RuntimeError("Database connection is not initialized")
        cursor = self.conn.execute(
            "SELECT last_sent_at FROM bot_link_reminders WHERE channel = ? AND chat_id = ?",
            (channel, chat_id),
        )
        row = cursor.fetchone()
        if row is None:
            return True
        try:
            last_sent_at = datetime.fromisoformat(str(row["last_sent_at"]))
        except Exception:
            return True
        return datetime.utcnow() - last_sent_at >= timedelta(seconds=max(1, cooldown_seconds))

    def mark_bot_link_reminder_sent(self, *, channel: str, chat_id: str) -> None:
        if self.conn is None:
            raise RuntimeError("Database connection is not initialized")
        now = datetime.utcnow().isoformat()
        self.conn.execute(
            """
            INSERT INTO bot_link_reminders (channel, chat_id, last_sent_at)
            VALUES (?, ?, ?)
            ON CONFLICT(channel, chat_id) DO UPDATE SET last_sent_at = excluded.last_sent_at
            """,
            (channel, chat_id, now),
        )
        self.conn.commit()

    def ensure_conversation(self, conversation_id: str, telegram_chat_id: str) -> None:
        if self.conn is None:
            raise RuntimeError("Database connection is not initialized")
        self.conn.execute(
            "INSERT OR IGNORE INTO telegram_conversations (conversation_id, telegram_chat_id) VALUES (?, ?)",
            (conversation_id, telegram_chat_id),
        )
        self.conn.execute(
            "UPDATE telegram_conversations SET last_updated = CURRENT_TIMESTAMP WHERE conversation_id = ?",
            (conversation_id,),
        )
        self.conn.commit()

    def add_message(self, conversation_id: str, role: str, content: str, message_type: str = "text") -> None:
        if self.conn is None:
            raise RuntimeError("Database connection is not initialized")
        self.conn.execute(
            "INSERT INTO telegram_messages (conversation_id, role, content, message_type) VALUES (?, ?, ?, ?)",
            (conversation_id, role, content, message_type),
        )
        self.conn.commit()

    def load_conversation_history(self, conversation_id: str) -> List[Dict[str, str]]:
        if self.conn is None:
            raise RuntimeError("Database connection is not initialized")
        cursor = self.conn.execute(
            "SELECT role, content FROM telegram_messages WHERE conversation_id = ? ORDER BY id ASC",
            (conversation_id,),
        )
        rows = cursor.fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in rows if row["content"] is not None]

    async def _run_agent_turn(
        self,
        conversation_id: str,
        run_id: str,
        user_id: str,
        messages: List[Dict[str, str]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        if self.app is None:
            raise RuntimeError("AI runtime is not initialized")

        messages_for_agent = _normalize_messages(messages)
        turn_context = _build_turn_context(user_id, metadata)

        if run_chat_turn is not None:
            result = run_chat_turn(
                app=self.app,
                messages=messages_for_agent,
                conversation_id=conversation_id,
                run_id=run_id,
                turn_context=turn_context,
                stream_mode="values",
                recursion_limit=20,
            )
            if inspect.isawaitable(result):
                result = await result
            return result

        if stream_chat_turn is not None:
            stream_gen = stream_chat_turn(
                app=self.app,
                messages=messages_for_agent,
                conversation_id=conversation_id,
                run_id=run_id,
                turn_context=turn_context,
                stream_mode="updates",
                recursion_limit=20,
            )
            if inspect.isawaitable(stream_gen):
                stream_gen = await stream_gen

            chunks = []
            if hasattr(stream_gen, "__aiter__"):
                async for item in stream_gen:
                    chunks.append(item)
            elif hasattr(stream_gen, "__iter__"):
                for item in stream_gen:
                    chunks.append(item)
            return chunks

        raise RuntimeError("No run_chat_turn or stream_chat_turn available in ai_agent_assistant")

    async def run_turn(
        self,
        conversation_uuid: str,
        run_uuid: str,
        user_id: str,
        messages: Optional[List[Union[Dict[str, str], Tuple[str, str]]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        if not self._initialized:
            raise RuntimeError("AI agent is not initialized")

        conversation_id = conversation_uuid
        if messages is None:
            messages = self.load_conversation_history(conversation_id)
        else:
            messages = _normalize_messages(messages)

        result = await self._run_agent_turn(conversation_id, run_uuid, user_id, messages, metadata)
        assistant_content = _extract_assistant_content_from_result(result)
        if assistant_content:
            self.add_message(conversation_id, "assistant", assistant_content)
        return assistant_content or "", {"result": result}

    async def chat(self, user_id: int, user_message: str) -> AsyncGenerator[str, None]:
        if not self._initialized:
            logger.error("AI agent not initialized")
            yield "❌ AI agent is not initialized. Please try again later."
            return

        conversation_id = f"telegram:{user_id}"
        self.ensure_telegram_user(str(user_id))
        self.ensure_conversation(conversation_id, str(user_id))
        self.add_message(conversation_id, "user", user_message)

        history = self.load_conversation_history(conversation_id)
        result = await self._run_agent_turn(
            conversation_id=conversation_id,
            run_id=uuid4().hex[:12],
            user_id=str(user_id),
            messages=history,
            metadata={"user_profile": {"channel": "telegram", "telegram_chat_id": str(user_id)}},
        )
        assistant_content = _extract_assistant_content_from_result(result)

        if assistant_content:
            self.add_message(conversation_id, "assistant", assistant_content)
            yield assistant_content
        else:
            logger.warning("No assistant content extracted from agent result")
            yield "⚠️ No response generated from AI agent."

    async def get_response(self, user_id: int, user_message: str, timeout: int = 30) -> str:
        try:
            response_parts: List[str] = []
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
        try:
            if self.conn is not None:
                conversation_id = f"telegram:{user_id}"
                self.conn.execute("DELETE FROM telegram_messages WHERE conversation_id = ?", (conversation_id,))
                self.conn.execute("DELETE FROM telegram_conversations WHERE conversation_id = ?", (conversation_id,))
                self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error clearing conversation for user {user_id}: {e}")
            return False

    def get_conversation_stats(self, user_id: int) -> dict:
        conversation_id = f"telegram:{user_id}"
        history = self.load_conversation_history(conversation_id) if self.conn is not None else []
        return {
            "user_id": user_id,
            "total_messages": len(history),
            "user_messages": sum(1 for m in history if m.get("role") == "user"),
            "assistant_messages": sum(1 for m in history if m.get("role") == "assistant"),
        }

    def configure_job_search(self, provider_fn: Callable[..., Any]) -> None:
        """Configure job search provider for the AI agent."""
        if configure_job_search_provider_fn is None:
            logger.warning("configure_job_search_provider is not available in ai_agent_assistant")
            return
        try:
            configure_job_search_provider_fn(provider_fn)
            logger.info("Job search provider configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure job search provider: {e}")


# Global AI integration instance
_ai_integration: Optional[AIAgentIntegration] = None


async def get_ai_integration(db_path: str = "ai_memory.db") -> AIAgentIntegration:
    global _ai_integration
    if _ai_integration is None:
        _ai_integration = AIAgentIntegration(db_path=db_path)
        await _ai_integration.initialize()
    return _ai_integration


async def chat_with_ai(user_id: int, message: str) -> AsyncGenerator[str, None]:
    integration = await get_ai_integration()
    async for chunk in integration.chat(user_id, message):
        yield chunk


async def get_ai_response(user_id: int, message: str, timeout: int = 30) -> str:
    integration = await get_ai_integration()
    return await integration.get_response(user_id, message, timeout=timeout)
