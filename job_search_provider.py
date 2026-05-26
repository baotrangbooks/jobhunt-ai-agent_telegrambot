from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _tool_args_preview(tool_args: dict[str, Any] | None) -> dict[str, Any]:
    payload = dict(tool_args or {})
    return {
        "query": str(payload.get("query", "")),
        "location": str(payload.get("location", "")),
        "location_norm": str(payload.get("location_norm", "")),
        "origin_address": str(payload.get("origin_address", "")),
        "origin_lat": payload.get("origin_lat"),
        "origin_lng": payload.get("origin_lng"),
        "radius_km": payload.get("radius_km"),
        "job_title": str(payload.get("job_title", "")),
        "salary_min": payload.get("salary_min"),
        "skills_count": len(payload.get("skills", []) or []),
        "keys": sorted(payload.keys()),
    }


def search_jobs_from_supabase_catalog(
    *,
    query: str,
    limit: int = 5,
    tool_args: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Telegram bot job provider using the same Supabase catalog as FastAPI."""

    from core.supabase_jobs import search_job_database_structured

    result = search_job_database_structured(query=query, limit=limit, tool_args=tool_args)
    logger.info(
        "telegram_job_search query=%r limit=%s tool_args=%s rows=%s",
        query,
        limit,
        _tool_args_preview(tool_args),
        len(result.get("rows", [])) if isinstance(result, dict) else 0,
    )
    return result


def configure_for_agent() -> callable:
    return search_jobs_from_supabase_catalog
