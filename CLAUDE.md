# Claude instructions for this repo

## job_matcher round reports (`job_matcher/reports/<date>-rd-lead-cpp-israel-roundN.md`)

When asked for a new round report:

- **Pull first** (`git pull`). Rounds are also generated from other sessions; take the next round number and deduplicate against every existing `job_matcher/reports/*.md`.
- **One report, all sources.** Each round MUST include results from ALL accessible job sources in a single report — LinkedIn, Greenhouse board API, Lever API, getajob.careers, Drushim, and any other board reachable without login. Never a LinkedIn-only round, never separate per-platform reports, and don't wait to be reminded.
- **Filters** (see `job_matcher/profile.example.yaml` `language_gate` / `hard_exclude_requirements`):
  - (a) requires C++ (even as an advantage, scored lower) AND role is R&D Team/Tech Lead **or** Senior SW Engineer/Developer; OR
  - (b) R&D Team/Tech Lead whose requirements name no specific programming language.
  - Drop postings that *require* (not merely list as nice-to-have) embedded, DSP, kernel, drivers, system-level/low-level work, OS/Windows/Linux internals, GPU/HW accelerators, or HW-SW interaction.
  - Location: center Israel only (exclude Haifa and north, Beer Sheva and south, Jerusalem). Drop closed postings.
- **Layout:** `## Strong fit` / `## Possible fit` / `## Weak fit`, each split into `### C++ Team/Tech Lead`, `### C++ Senior`, `### Team/Tech Lead, no specific SW language`. Omit empty levels/subsections. No "checked and dropped" section; keep entries short.
- **Commit and push** the report when done.
