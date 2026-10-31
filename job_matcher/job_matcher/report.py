"""Render match results to a Markdown report and a raw JSON dump."""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .matcher import MatchResult

_VERDICT_EMOJI = {
    "strong_fit": "🟢",
    "possible_fit": "🟡",
    "weak_fit": "🟠",
    "not_fit": "🔴",
    "error": "⚠️",
    "unknown": "❔",
}

# This subject line and filename slug are specific to the R&D team lead /
# tech lead / C++ / Israel search this tool has been run for -- update them
# directly if the search's profile changes.
REPORT_SUBJECT = "R&D Team Lead / Tech Lead — Israel, C++ background"
REPORT_SLUG = "rd-lead-cpp-israel"

_ROUND_RE = re.compile(re.escape(REPORT_SLUG) + r"-round(\d+)\.md$")

# Report layout: fit level first, then which language-gate path the posting
# qualified through. Empty levels/categories are left out entirely.
_FIT_LEVELS = [
    ("strong_fit", "Strong fit"),
    ("possible_fit", "Possible fit"),
    ("weak_fit", "Weak fit"),
]
_CATEGORIES = [
    ("required_language_lead", "C++ Team/Tech Lead"),
    ("required_language_senior", "C++ Senior"),
    ("language_agnostic_leadership", "Team/Tech Lead, no specific SW language"),
    ("", "Other"),
]
# Older results recorded the C++ path without the lead/senior split.
_CATEGORY_ALIASES = {"required_language": "required_language_lead"}


def _category_of(r: MatchResult) -> str:
    qv = _CATEGORY_ALIASES.get(r.qualified_via, r.qualified_via)
    known = {key for key, _ in _CATEGORIES}
    return qv if qv in known else ""


def next_round_number(reports_dir: str | Path) -> int:
    """Inspect `reports_dir` for existing `...-round<N>.md` reports and
    return the next round number (1 if none exist yet)."""
    dir_path = Path(reports_dir)
    if not dir_path.is_dir():
        return 1
    found = [
        int(m.group(1))
        for f in dir_path.iterdir()
        if (m := _ROUND_RE.search(f.name))
    ]
    return max(found, default=0) + 1


def default_report_path(reports_dir: str | Path, round_num: int) -> Path:
    """Build the standard `<date>-<slug>-round<N>.md` path for this search."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return Path(reports_dir) / f"{today}-{REPORT_SLUG}-round{round_num}.md"


def write_markdown(
    results: list[MatchResult], path: str | Path, round_num: int
) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines: list[str] = [
        f"# {REPORT_SUBJECT} — round {round_num} — {today}",
        "",
    ]

    for verdict, level_title in _FIT_LEVELS:
        in_level = [r for r in results if not r.excluded and r.verdict == verdict]
        if not in_level:
            continue
        lines.append(f"## {level_title}")
        lines.append("")
        for category, category_title in _CATEGORIES:
            in_cat = sorted(
                (r for r in in_level if _category_of(r) == category),
                key=lambda r: r.score,
                reverse=True,
            )
            if not in_cat:
                continue
            lines.append(f"### {category_title}")
            lines.append("")
            for r in in_cat:
                _append_entry(lines, r)

    Path(path).write_text("\n".join(lines), encoding="utf-8")


def _append_entry(lines: list[str], r: MatchResult) -> None:
    emoji = _VERDICT_EMOJI.get(r.verdict, "❔")
    lines.append(f"#### {emoji} {r.score} — {r.job.title} @ {r.job.company}")
    lines.append("")
    meta_bits = [b for b in [r.job.location, r.job.source] if b]
    if meta_bits:
        lines.append(" · ".join(meta_bits) + "  ")
    if r.job.url:
        lines.append(f"[View posting]({r.job.url})")
    lines.append("")

    if r.error:
        lines.append(f"**Error:** {r.error}")
        lines.append("")
        return

    if r.reasoning:
        lines.append(r.reasoning)
        lines.append("")
    if r.matched_requirements:
        lines.append("**Matches:**")
        lines.extend(f"- {item}" for item in r.matched_requirements)
        lines.append("")
    if r.missing_requirements:
        lines.append("**Gaps:**")
        lines.extend(f"- {item}" for item in r.missing_requirements)
        lines.append("")
    if r.preference_notes:
        lines.append("**Preference fit:**")
        lines.extend(f"- {item}" for item in r.preference_notes)
        lines.append("")

    lines.append("---")
    lines.append("")


def write_json(results: list[MatchResult], path: str | Path) -> None:
    kept = [r for r in results if not r.excluded]
    ranked = sorted(kept, key=lambda r: r.score, reverse=True)
    payload = []
    for r in ranked:
        d = asdict(r)
        d["job"] = {
            "id": r.job.id,
            "title": r.job.title,
            "company": r.job.company,
            "url": r.job.url,
            "source": r.job.source,
            "location": r.job.location,
            "remote": r.job.remote,
        }
        payload.append(d)
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
