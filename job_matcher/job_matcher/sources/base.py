"""Shared job-posting model used by every source fetcher."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class JobPosting:
    """A normalized job posting, regardless of which board it came from."""

    id: str
    title: str
    company: str
    url: str
    source: str
    location: str = ""
    remote: bool | None = None
    description: str = ""
    department: str = ""
    posted_at: str = ""
    raw: dict = field(default_factory=dict, repr=False)

    def fingerprint(self) -> str:
        """Stable id used for de-duplication and skip-list caching."""
        return f"{self.source}:{self.id}"
