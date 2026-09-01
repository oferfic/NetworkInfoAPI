"""Fetch job postings from a company's public Lever job board.

No API key needed -- Lever exposes a public, unauthenticated JSON API per
company:

    https://api.lever.co/v0/postings/{company}?mode=json

``company`` is the slug in the company's public Lever careers URL, e.g.
https://jobs.lever.co/figma -> company "figma".
"""

from __future__ import annotations

import logging

import requests

from ..html_utils import html_to_text
from .base import JobPosting

logger = logging.getLogger(__name__)

_API_URL = "https://api.lever.co/v0/postings/{company}"


def fetch_jobs(company: str, timeout: int = 20) -> list[JobPosting]:
    """Fetch all open postings for one Lever company."""
    resp = requests.get(
        _API_URL.format(company=company),
        params={"mode": "json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    payload = resp.json()

    postings: list[JobPosting] = []
    for job in payload:
        categories = job.get("categories") or {}
        location = categories.get("location", "") or ""
        lists = job.get("lists") or []
        description_parts = [html_to_text(job.get("descriptionHtml", ""))]
        for section in lists:
            text = html_to_text(section.get("content", ""))
            if text:
                description_parts.append(f"## {section.get('text', '')}\n{text}")
        postings.append(
            JobPosting(
                id=str(job.get("id")),
                title=job.get("text", "").strip(),
                company=company,
                url=job.get("hostedUrl", ""),
                source="lever",
                location=location,
                remote=_looks_remote(location, categories.get("commitment", "")),
                description="\n\n".join(p for p in description_parts if p),
                department=categories.get("team", ""),
                posted_at=str(job.get("createdAt", "")),
                raw=job,
            )
        )
    return postings


def _looks_remote(location: str, commitment: str) -> bool | None:
    haystack = f"{location} {commitment}".lower()
    if "remote" in haystack:
        return True
    return None
