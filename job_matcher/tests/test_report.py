import tempfile
import unittest
from pathlib import Path

from job_matcher.matcher import MatchResult
from job_matcher.report import write_markdown
from job_matcher.sources.base import JobPosting


def _job(**overrides):
    defaults = dict(
        id="1",
        title="Backend Engineer",
        company="Acme",
        url="https://example.com/1",
        source="greenhouse",
        location="Remote",
        remote=True,
        description="desc",
    )
    defaults.update(overrides)
    return JobPosting(**defaults)


class WriteMarkdownTest(unittest.TestCase):
    def _write(self, results):
        tmp = Path(tempfile.mkstemp(suffix=".md")[1])
        self.addCleanup(tmp.unlink)
        write_markdown(results, tmp)
        return tmp.read_text(encoding="utf-8")

    def test_excluded_results_go_to_their_own_section_not_ranked_list(self):
        kept = MatchResult(
            job=_job(id="1", title="Backend Engineer"),
            score=80,
            verdict="strong_fit",
        )
        dropped = MatchResult(
            job=_job(id="2", title="Embedded Engineer"),
            score=0,
            verdict="not_fit",
            excluded=True,
            excluded_because="Requires 'embedded': 5+ years embedded development.",
        )
        text = self._write([kept, dropped])

        self.assertIn("Backend Engineer @ Acme", text)
        self.assertIn("## Excluded (hard filter)", text)
        self.assertIn("Embedded Engineer @ Acme", text)
        self.assertIn("Requires 'embedded'", text)
        # The excluded posting must not appear as a normal ranked "## <emoji> <score>" entry.
        self.assertNotIn("## 🔴 0 — Embedded Engineer", text)

    def test_no_excluded_section_when_nothing_excluded(self):
        kept = MatchResult(job=_job(), score=50, verdict="possible_fit")
        text = self._write([kept])
        self.assertNotIn("Excluded (hard filter)", text)


if __name__ == "__main__":
    unittest.main()
