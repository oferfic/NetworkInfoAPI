"""Score a job posting against your profile using the Claude API."""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field

import anthropic

from .config import Profile
from .sources.base import JobPosting

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-5"

# Descriptions can be long; cap what we send to keep cost/latency sane. Most
# postings' actual requirements land well inside this budget.
_MAX_DESCRIPTION_CHARS = 8000

_SYSTEM_PROMPT = """\
You are a career-fit evaluator helping a candidate triage job postings quickly and honestly.

You will be given:
1. The candidate's background and preferences.
2. One job posting: title, company, location, and full description.

Do this:
1. Locate the requirements/qualifications section within the job description \
(it may be labeled "Requirements", "Qualifications", "What you'll need", \
"You have", "Must haves", "Minimum qualifications", etc. -- postings vary). \
If there's no distinct section, treat the whole description as the requirements signal.
2. Compare those requirements point-by-point against the candidate's background \
(skills, years of experience, seniority, domain knowledge).
3. Separately check the posting against the candidate's stated preferences \
(location/remote policy, seniority/title, company stage or size, comp if mentioned, \
and anything else they listed) as far as the posting actually reveals them. \
Do not penalize the posting for preference information it simply doesn't mention.
4. Score overall fit 0-100 and pick a verdict: "strong_fit" (score >= 75), \
"possible_fit" (45-74), or "not_fit" (< 45).
5. Be specific and honest -- name real gaps instead of flattering. If the \
description doesn't give you enough to judge something, say so in reasoning \
rather than guessing.

Respond with ONLY a single JSON object -- no prose outside it, no markdown fences:
{
  "score": <integer 0-100>,
  "verdict": "strong_fit" | "possible_fit" | "not_fit",
  "matched_requirements": [<short strings: requirements the candidate clearly meets>],
  "missing_requirements": [<short strings: requirements the candidate likely doesn't meet or that are unclear>],
  "preference_notes": [<short strings: how the posting lines up with stated preferences>],
  "reasoning": "<2-4 sentence plain-English summary of the verdict>"
}
"""


@dataclass
class MatchResult:
    job: JobPosting
    score: int
    verdict: str
    matched_requirements: list[str] = field(default_factory=list)
    missing_requirements: list[str] = field(default_factory=list)
    preference_notes: list[str] = field(default_factory=list)
    reasoning: str = ""
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


class Matcher:
    def __init__(
        self,
        profile: Profile,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
    ) -> None:
        self.profile = profile
        self.model = model
        resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not resolved_key:
            raise RuntimeError(
                "No Anthropic API key found. Set ANTHROPIC_API_KEY in your "
                "environment (or a .env file) before running the matcher."
            )
        self.client = anthropic.Anthropic(api_key=resolved_key)

    def evaluate(self, job: JobPosting) -> MatchResult:
        """Score one job posting against the loaded profile."""
        prompt = _build_prompt(self.profile, job)
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:  # noqa: BLE001 - surface any SDK error as a result
            logger.warning(
                "LLM call failed for %r at %r: %s", job.title, job.company, exc
            )
            return MatchResult(
                job=job,
                score=0,
                verdict="error",
                error=str(exc),
            )

        text = "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        )
        data = _parse_json_response(text)
        if data is None:
            logger.warning(
                "Could not parse LLM response as JSON for %r at %r", job.title, job.company
            )
            return MatchResult(
                job=job,
                score=0,
                verdict="error",
                reasoning=text[:500],
                error="Could not parse LLM response as JSON",
            )

        return MatchResult(
            job=job,
            score=_coerce_score(data.get("score")),
            verdict=str(data.get("verdict", "unknown")),
            matched_requirements=list(data.get("matched_requirements", []) or []),
            missing_requirements=list(data.get("missing_requirements", []) or []),
            preference_notes=list(data.get("preference_notes", []) or []),
            reasoning=str(data.get("reasoning", "")),
        )


def _build_prompt(profile: Profile, job: JobPosting) -> str:
    description = job.description or "(no description text was available)"
    if len(description) > _MAX_DESCRIPTION_CHARS:
        description = description[:_MAX_DESCRIPTION_CHARS] + "\n...[truncated]"

    return f"""\
## Candidate background and preferences

{profile.as_prompt_text()}

## Job posting

Title: {job.title}
Company: {job.company}
Location: {job.location or "(not specified)"}
Remote: {job.remote if job.remote is not None else "(unclear from listing)"}
Source: {job.source}
URL: {job.url}

Description:
{description}
"""


def _coerce_score(value) -> int:
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError):
        return 0
    return max(0, min(100, score))


_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_json_response(text: str) -> dict | None:
    text = text.strip()
    # Strip accidental markdown code fences even though the prompt forbids them.
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = _JSON_OBJECT_RE.search(text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None
