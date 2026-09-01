# Job Matcher

A small CLI that pulls open R&D/tech job postings from public job-board
APIs and scores each one against your background and preferences using
Claude, focusing specifically on how well you match the requirements
section.

## How it works

1. You describe your background and preferences once, in `profile.yaml`.
2. You list which companies/boards to pull from in `sources.yaml`
   (Greenhouse and Lever company boards, plus RemoteOK), with optional
   keyword filters to control volume.
3. `job_matcher run` fetches postings, sends each one (title + full
   description) to Claude alongside your profile, and asks it to locate the
   requirements section, compare it to your background, and rate the fit.
4. You get a Markdown report (and optionally raw JSON) ranked by score,
   with per-posting matched requirements, gaps, and preference notes.

No scraping, no browser automation, no ToS-risky sites -- only official
public JSON APIs that Greenhouse, Lever, and RemoteOK expose for their job
boards.

## Setup

```bash
cd job_matcher
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp profile.example.yaml profile.yaml     # fill in your background/preferences
cp sources.example.yaml sources.yaml     # list the companies/boards to search
cp .env.example .env                     # add your ANTHROPIC_API_KEY
```

Edit `profile.yaml` and `sources.yaml` -- see the comments in each example
file for the fields the matcher prompt makes best use of, and how to find a
company's Greenhouse/Lever board token from its careers page.

## Run

```bash
python -m job_matcher.cli run
```

Options:

```
--profile PATH        path to profile.yaml (default: profile.yaml)
--sources PATH         path to sources.yaml (default: sources.yaml)
--output PATH          markdown report path (default: report.md)
--json-output PATH     also write raw results as JSON
--model MODEL_ID       Claude model to use (default: claude-sonnet-5)
--limit N              cap how many postings get evaluated (useful for a dry run)
--delay SECONDS        sleep between LLM calls
-v, --verbose          debug logging
```

Example: a quick, cheap dry run against just a few postings before
committing to a full pass:

```bash
python -m job_matcher.cli run --limit 5 -v
```

## Adding job sources

- **Greenhouse**: find the company's careers URL, e.g.
  `https://job-boards.greenhouse.io/<token>` -- add `<token>` under
  `greenhouse_boards` in `sources.yaml`.
- **Lever**: find the company's careers URL, e.g.
  `https://jobs.lever.co/<company>` -- add `<company>` under
  `lever_companies`.
- **RemoteOK**: set `remoteok.enabled: true` and list tags (e.g. `backend`,
  `senior`) under `remoteok.tags`; RemoteOK is a single shared feed, so this
  is more of a broad supplement than a per-company source.

Other boards with a public, unauthenticated JSON API (e.g. Ashby,
SmartRecruiters) can be added the same way -- drop a new module in
`job_matcher/sources/` that returns a list of `JobPosting`, matching the
shape of `greenhouse.py` or `lever.py`, and wire it into `cli.py`'s
`_fetch_all`.

## Notes on cost

Each posting costs one Claude API call. `keywords` / `exclude_keywords` in
`sources.yaml` filter by title *before* any LLM call, so tighten those
first if you want to control spend. `--limit` and `--delay` are there for
the same reason during testing.

## Tests

```bash
pip install pytest
pytest
```

Tests mock all HTTP and LLM calls -- no network or API key required to run
them.
