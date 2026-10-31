"""Fetch job postings from Elbit Systems' own careers site.

elbitsystemscareer.com is a JS-rendered site, but it loads every open
position from one public, unauthenticated JSON feed:

    https://elbitsystemscareer.com/cron/jobs.json

Each entry has the full description/requirements plus an ``area`` field
(e.g. "Center", "Sharon", "Shfela", "North", "Haifa", "South",
"Jerusalem Area"), which we use as the location and to filter by region.
Job pages aren't linkable by id, so the posting URL points at the site's
job search and the job id/code is put in the title line of the description.
"""

from __future__ import annotations

import html
import logging

import requests

from ..html_utils import html_to_text
from .base import JobPosting

logger = logging.getLogger(__name__)

FEED_URL = "https://elbitsystemscareer.com/cron/jobs.json"
JOBS_PAGE_URL = "https://elbitsystemscareer.com/jobs"


def fetch_jobs(areas: list[str] | None = None, timeout: int = 60) -> list[JobPosting]:
    """Fetch all open Elbit postings, optionally keeping only `areas`
    (case-insensitive match on the feed's ``area`` field)."""
    resp = requests.get(FEED_URL, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    payload = resp.json()

    wanted = {a.lower() for a in areas or []}
    postings: list[JobPosting] = []
    for job in payload:
        area = (job.get("area") or "").strip()
        if wanted and area.lower() not in wanted:
            continue
        # The feed HTML-escapes its HTML, so unescape once before stripping tags.
        parts = [
            html_to_text(html.unescape(job.get(key) or ""))
            for key in ("description", "requirements", "skills")
        ]
        job_id = str(job.get("jobId", ""))
        header = f"Elbit job id {job_id}, code {job.get('jobCode', '')}"
        postings.append(
            JobPosting(
                id=job_id,
                title=(job.get("jobTitle") or "").strip(),
                company="Elbit Systems",
                url=JOBS_PAGE_URL,
                source="elbit",
                location=area,
                remote=None,
                description="\n\n".join([header] + [p for p in parts if p]),
                posted_at=job.get("updateDate") or job.get("openDate") or "",
                raw=job,
            )
        )
    return postings
