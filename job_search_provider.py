"""
Job Search Provider for Telegram Bot
Mock implementation for job search functionality
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


# Mock job database
MOCK_JOBS = [
    {
        "id": "job_001",
        "title": "Python Developer",
        "company": "Tech Corp",
        "location": "Ho Chi Minh City",
        "salary": "$2000 - $3000",
        "description": "Looking for experienced Python developers to build AI solutions.",
    },
    {
        "id": "job_002",
        "title": "Full Stack Developer",
        "company": "StartupXYZ",
        "location": "Hanoi",
        "salary": "$1500 - $2500",
        "description": "Join our team to develop web applications with FastAPI and React.",
    },
    {
        "id": "job_003",
        "title": "Data Scientist",
        "company": "DataCorp",
        "location": "Da Nang",
        "salary": "$2500 - $3500",
        "description": "Help us build machine learning models to analyze user behavior.",
    },
    {
        "id": "job_004",
        "title": "DevOps Engineer",
        "company": "CloudInc",
        "location": "Ho Chi Minh City, Hanoi",
        "salary": "$2000 - $3000",
        "description": "Manage and optimize our Kubernetes infrastructure on AWS.",
    },
]


async def search_jobs(
    query: str = "",
    location: Optional[str] = None,
    salary_min: Optional[float] = None,
    salary_max: Optional[float] = None,
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """
    Search for jobs based on criteria.

    Args:
        query: Job title or keywords to search
        location: Job location
        salary_min: Minimum salary
        salary_max: Maximum salary
        **kwargs: Additional filters

    Returns:
        List of matching jobs
    """
    logger.info(f"Searching jobs: query={query}, location={location}")

    results = []
    query_lower = query.lower() if query else ""

    for job in MOCK_JOBS:
        # Filter by query (title/description)
        if query_lower and query_lower not in job["title"].lower() and query_lower not in job["description"].lower():
            continue

        # Filter by location
        if location and location.lower() not in job["location"].lower():
            continue

        results.append(job)

    logger.info(f"Found {len(results)} jobs matching criteria")
    return results


async def get_job_details(job_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific job."""
    for job in MOCK_JOBS:
        if job["id"] == job_id:
            return job
    return None


def configure_for_agent() -> callable:
    """
    Get the configured job search function for the AI agent.
    This should be called to configure the agent with job search capabilities.
    """
    return search_jobs
