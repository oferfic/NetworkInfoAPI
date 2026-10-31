# Claude instructions for this repo

## job_matcher round reports (`job_matcher/reports/<date>-rd-lead-cpp-israel-roundN.md`)

When asked for a new round report:

- **Pull first** (`git pull`). Rounds are also generated from other sessions; take the next round number and deduplicate against every existing `job_matcher/reports/*.md`.
- **One report, all sources.** Each round MUST include results from ALL accessible job sources in a single report — LinkedIn, Greenhouse board API, Lever API, **Elbit's own feed** (`https://elbitsystemscareer.com/cron/jobs.json`, `area` Center/Sharon/Shfela), getajob.careers, Drushim, and any other board reachable without login. Never a LinkedIn-only round, never separate per-platform reports, and don't wait to be reminded. IAI's site blocks bots — cover IAI via LinkedIn.
- **Read each candidate posting** (requirements, not just the title) before including it.
- **Filters** (see `job_matcher/profile.example.yaml` `language_gate` / `hard_exclude_requirements`):
  - (a) requires C++ (even as an advantage, scored lower) AND role is R&D Team/Tech Lead **or** Senior SW Engineer/Developer; OR
  - (b) R&D Team/Tech Lead whose requirements name no specific programming language.
  - Drop postings (from ANY source) that *require* (not merely list as nice-to-have) embedded, DSP, kernel, drivers, system-level/low-level work, OS/Windows/Linux internals, GPU/HW accelerators, HW-SW interaction, **real-time (RT/RTOS)**, **computer vision / image processing**, or robotics/control systems. A term in the job title counts as required.
  - Drop Group-Manager-level roles that require managing team leads, and hardware/RF/system-integration roles (not software).
  - Location: center Israel only (exclude Haifa and north, Jerusalem, Beer Sheva and south; Ashdod is acceptable as the southern edge). Drop closed postings.
- **Layout:** `## Strong fit` / `## Possible fit` / `## Weak fit`, each split into `### C++ Team/Tech Lead`, `### C++ Senior`, `### Team/Tech Lead, no specific SW language`. Omit empty levels/subsections. No "checked and dropped" section; keep entries short.
- **Commit and push** the report when done.
