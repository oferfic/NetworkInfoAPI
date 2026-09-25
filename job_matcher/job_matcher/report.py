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
    kept = [
        r for r in results
        if not r.excluded and r.verdict in ("strong_fit", "possible_fit")
    ]
    ranked = sorted(kept, key=lambda r: r.score, reverse=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines: list[str] = [
        f"# {REPORT_SUBJECT} — round {round_num} — {today}",
        "",
    ]

    for r in ranked:
        emoji = _VERDICT_EMOJI.get(r.verdict, "❔")
        lines.append(f"## {emoji} {r.score} — {r.job.title} @ {r.job.company}")
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
            continue

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

    Path(path).write_text("\n".join(lines), encoding="utf-8")


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
