"""Fetch job postings from the public RemoteOK API.

No API key needed:

    https://remoteok.com/api

Returns a JSON array whose first element is a legal/metadata notice (no
``id`` field) followed by job postings. RemoteOK doesn't support real
server-side filtering on this endpoint, so we fetch the full feed once and
filter locally by tag/keyword.
"""

from __future__ import annotations

import logging

import requests

from ..html_utils import html_to_text
from .base import JobPosting

logger = logging.getLogger(__name__)

_API_URL = "https://remoteok.com/api"


def fetch_jobs(
    tags: list[str] | None = None,
    keywords: list[str] | None = None,
    timeout: int = 20,
) -> list[JobPosting]:
    """Fetch RemoteOK postings, optionally filtered by tag or keyword.

    A job is kept if it matches ANY of ``tags`` (checked against RemoteOK's
    own tag list) OR ANY of ``keywords`` (checked against the title). If
    neither is given, every posting is returned.
    """
    resp = requests.get(
        _API_URL,
        timeout=timeout,
        headers={"User-Agent": "job-matcher (personal use)"},
    )
    resp.raise_for_status()
    payload = resp.json()

    tags_lower = {t.lower() for t in (tags or [])}
    keywords_lower = [k.lower() for k in (keywords or [])]

    postings: list[JobPosting] = []
    for job in payload:
        if "id" not in job:
            continue  # the legal notice row

        job_tags = {str(t).lower() for t in (job.get("tags") or [])}
        title = (job.get("position") or "").strip()

        if tags_lower or keywords_lower:
            tag_hit = bool(job_tags & tags_lower)
            keyword_hit = any(k in title.lower() for k in keywords_lower)
            if not (tag_hit or keyword_hit):
                continue

        postings.append(
            JobPosting(
                id=str(job.get("id")),
                title=title,
                company=job.get("company", ""),
                url=job.get("url", ""),
                source="remoteok",
                location=job.get("location", ""),
                remote=True,
                description=html_to_text(job.get("description", "")),
                department="",
                posted_at=job.get("date", ""),
                raw=job,
            )
        )
    return postings
