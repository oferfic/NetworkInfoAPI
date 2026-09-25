"""Render match results to a Markdown report and a raw JSON dump."""

from __future__ import annotations

import json
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


def write_markdown(results: list[MatchResult], path: str | Path) -> None:
    kept = [
        r for r in results
        if not r.excluded and r.verdict in ("strong_fit", "possible_fit")
    ]
    ranked = sorted(kept, key=lambda r: r.score, reverse=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines: list[str] = [
        "# Job match report",
        "",
        f"Generated: {generated_at}  ",
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
