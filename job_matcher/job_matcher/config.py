"""Load and validate the two user-editable config files.

``profile.yaml``  -- your background + preferences (free-form-ish, but see
                     profile.example.yaml for the fields the matcher prompt
                     knows how to use best).
``sources.yaml``  -- which job boards to pull from, and any keyword filter
                     to narrow the fetch before spending LLM calls on it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"Config file not found: {p}\n"
            f"Copy the matching *.example.yaml next to it and edit it first."
        )
    with p.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{p} must contain a YAML mapping at the top level")
    return data


@dataclass
class Profile:
    """Your background + preferences, as free text handed to the LLM.

    Deliberately loose: the source YAML can contain whatever sections and
    fields make sense to you (background, preferences, deal_breakers, ...).
    We keep the parsed dict around and also render it to readable text once,
    so the matcher prompt doesn't need to know the exact schema.
    """

    raw: dict[str, Any]

    @classmethod
    def load(cls, path: str | Path) -> "Profile":
        return cls(raw=_load_yaml(path))

    def as_prompt_text(self) -> str:
        return _yaml_block(self.raw)


@dataclass
class SourcesConfig:
    greenhouse_boards: list[str] = field(default_factory=list)
    lever_companies: list[str] = field(default_factory=list)
    remoteok_enabled: bool = False
    remoteok_tags: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    exclude_keywords: list[str] = field(default_factory=list)
    max_jobs_per_source: int = 50

    @classmethod
    def load(cls, path: str | Path) -> "SourcesConfig":
        data = _load_yaml(path)
        remoteok = data.get("remoteok") or {}
        return cls(
            greenhouse_boards=list(data.get("greenhouse_boards") or []),
            lever_companies=list(data.get("lever_companies") or []),
            remoteok_enabled=bool(remoteok.get("enabled", False)),
            remoteok_tags=list(remoteok.get("tags") or []),
            keywords=[k.lower() for k in (data.get("keywords") or [])],
            exclude_keywords=[
                k.lower() for k in (data.get("exclude_keywords") or [])
            ],
            max_jobs_per_source=int(data.get("max_jobs_per_source", 50)),
        )

    def title_matches_keywords(self, title: str) -> bool:
        """True if the title should be kept, given configured keyword filters."""
        title_lower = title.lower()
        if self.exclude_keywords and any(
            k in title_lower for k in self.exclude_keywords
        ):
            return False
        if not self.keywords:
            return True
        return any(k in title_lower for k in self.keywords)


def _yaml_block(data: dict[str, Any]) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True).strip()
