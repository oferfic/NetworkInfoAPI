"""Command-line entry point.

Usage:
    python -m job_matcher.cli run \\
        --profile profile.yaml --sources sources.yaml --output report.md
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from .config import Profile, SourcesConfig
from .matcher import DEFAULT_MODEL, Matcher
from .report import write_json, write_markdown
from .sources import JobPosting
from .sources import greenhouse, lever, remoteok

logger = logging.getLogger("job_matcher")


def _fetch_all(sources: SourcesConfig) -> list[JobPosting]:
    jobs: list[JobPosting] = []
    seen: set[str] = set()

    def _collect(fetched: list[JobPosting], label: str) -> None:
        kept = 0
        for job in fetched[: sources.max_jobs_per_source]:
            if not sources.title_matches_keywords(job.title):
                continue
            fp = job.fingerprint()
            if fp in seen:
                continue
            seen.add(fp)
            jobs.append(job)
            kept += 1
        logger.info("%s: fetched %d, kept %d after filters", label, len(fetched), kept)

    for board in sources.greenhouse_boards:
        try:
            _collect(greenhouse.fetch_jobs(board), f"greenhouse/{board}")
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to fetch greenhouse board %r: %s", board, exc)

    for company in sources.lever_companies:
        try:
            _collect(lever.fetch_jobs(company), f"lever/{company}")
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to fetch lever company %r: %s", company, exc)

    if sources.remoteok_enabled:
        try:
            fetched = remoteok.fetch_jobs(
                tags=sources.remoteok_tags, keywords=sources.keywords
            )
            _collect(fetched, "remoteok")
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to fetch remoteok: %s", exc)

    return jobs


def cmd_run(args: argparse.Namespace) -> int:
    profile = Profile.load(args.profile)
    sources = SourcesConfig.load(args.sources)

    logger.info("Fetching postings...")
    jobs = _fetch_all(sources)
    if args.limit:
        jobs = jobs[: args.limit]
    logger.info("Evaluating %d postings against your profile...", len(jobs))

    if not jobs:
        print("No postings matched your source config's keyword filters.")
        return 0

    matcher = Matcher(profile, model=args.model)
    results = []
    for i, job in enumerate(jobs, start=1):
        logger.info("[%d/%d] %s @ %s", i, len(jobs), job.title, job.company)
        results.append(matcher.evaluate(job))
        if args.delay:
            time.sleep(args.delay)

    write_markdown(results, args.output)
    if args.json_output:
        write_json(results, args.json_output)

    strong = sum(1 for r in results if r.verdict == "strong_fit")
    possible = sum(1 for r in results if r.verdict == "possible_fit")
    excluded = sum(1 for r in results if r.excluded)
    errors = sum(1 for r in results if not r.ok)
    print(
        f"Done. {len(results)} evaluated: {strong} strong fit, "
        f"{possible} possible fit, {excluded} hard-excluded, "
        f"{errors} errors. Report: {args.output}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="job_matcher",
        description="Search tech job postings and score them against your profile.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logging."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Fetch postings and score them.")
    run.add_argument("--profile", default="profile.yaml", help="Path to profile.yaml")
    run.add_argument("--sources", default="sources.yaml", help="Path to sources.yaml")
    run.add_argument("--output", default="report.md", help="Markdown report path")
    run.add_argument(
        "--json-output", default=None, help="Optional path to also write raw JSON"
    )
    run.add_argument("--model", default=DEFAULT_MODEL, help="Claude model id")
    run.add_argument(
        "--limit", type=int, default=None, help="Cap the number of postings evaluated"
    )
    run.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Seconds to sleep between LLM calls (basic rate-limit courtesy)",
    )
    run.set_defaults(func=cmd_run)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
