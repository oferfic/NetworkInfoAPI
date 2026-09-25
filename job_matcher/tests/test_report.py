import os
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
        fd, name = tempfile.mkstemp(suffix=".md")
        os.close(fd)  # avoid a lingering handle blocking cleanup on Windows
        tmp = Path(name)
        self.addCleanup(tmp.unlink)
        write_markdown(results, tmp)
        return tmp.read_text(encoding="utf-8")

    def test_excluded_results_are_left_out_of_the_report_entirely(self):
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
        # Excluded postings must not appear anywhere -- no section, no mention.
        self.assertNotIn("Embedded Engineer", text)
        self.assertNotIn("Excluded", text)
        self.assertNotIn("excluded", text)
        self.assertNotIn("Requires 'embedded'", text)

    def test_no_excluded_section_when_nothing_excluded(self):
        kept = MatchResult(job=_job(), score=50, verdict="possible_fit")
        text = self._write([kept])
        self.assertNotIn("Excluded", text)

    def test_not_fit_results_are_left_out_of_the_report(self):
        fit = MatchResult(
            job=_job(id="1", title="Backend Engineer"),
            score=80,
            verdict="strong_fit",
        )
        no_fit = MatchResult(
            job=_job(id="2", title="Sales Manager"),
            score=10,
            verdict="not_fit",
        )
        text = self._write([fit, no_fit])

        self.assertIn("Backend Engineer @ Acme", text)
        self.assertNotIn("Sales Manager", text)


if __name__ == "__main__":
    unittest.main()
