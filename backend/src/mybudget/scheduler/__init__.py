"""
Scheduler module for background task scheduling.

This module provides the APScheduler-based scheduler singleton
for running background tasks like bank sync operations.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Global scheduler instance (singleton)
scheduler = AsyncIOScheduler(
    job_defaults={
        "coalesce": True,  # Combine multiple missed runs into one
        "max_instances": 1,  # Only one instance of each job at a time
        "misfire_grace_time": 60,  # Grace period for missed jobs (seconds)
    }
)


def get_scheduler() -> AsyncIOScheduler:
    """Get the global scheduler instance."""
    return scheduler


__all__ = ["scheduler", "get_scheduler"]
