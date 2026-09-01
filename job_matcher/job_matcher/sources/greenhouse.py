"""Fetch job postings from a company's public Greenhouse job board.

No API key needed -- Greenhouse exposes a public, unauthenticated JSON API
per company board:

    https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true

``board_token`` is the slug Greenhouse assigns the company, visible in the
company's public careers URL, e.g. https://job-boards.greenhouse.io/stripe
-> board_token "stripe".
"""

from __future__ import annotations

import logging

import requests

from ..html_utils import html_to_text
from .base import JobPosting

logger = logging.getLogger(__name__)

_API_URL = "https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"


def fetch_jobs(board_token: str, timeout: int = 20) -> list[JobPosting]:
    """Fetch all open postings for one Greenhouse board."""
    resp = requests.get(
        _API_URL.format(board_token=board_token),
        params={"content": "true"},
        timeout=timeout,
    )
    resp.raise_for_status()
    payload = resp.json()

    postings: list[JobPosting] = []
    for job in payload.get("jobs", []):
        location = (job.get("location") or {}).get("name", "")
        departments = job.get("departments") or []
        department = departments[0]["name"] if departments else ""
        postings.append(
            JobPosting(
                id=str(job.get("id")),
                title=job.get("title", "").strip(),
                company=board_token,
                url=job.get("absolute_url", ""),
                source="greenhouse",
                location=location,
                remote=_looks_remote(location, job.get("title", "")),
                description=html_to_text(job.get("content", "")),
                department=department,
                posted_at=job.get("updated_at", ""),
                raw=job,
            )
        )
    return postings


def _looks_remote(location: str, title: str) -> bool | None:
    haystack = f"{location} {title}".lower()
    if "remote" in haystack:
        return True
    return None
