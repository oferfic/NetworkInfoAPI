import os
import tempfile
import unittest
from pathlib import Path

from job_matcher.matcher import MatchResult
from job_matcher.report import default_report_path, next_round_number, write_markdown
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
    def _write(self, results, round_num=1):
        fd, name = tempfile.mkstemp(suffix=".md")
        os.close(fd)  # avoid a lingering handle blocking cleanup on Windows
        tmp = Path(name)
        self.addCleanup(tmp.unlink)
        write_markdown(results, tmp, round_num=round_num)
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

    def test_title_includes_round_number(self):
        kept = MatchResult(job=_job(), score=80, verdict="strong_fit")
        text = self._write([kept], round_num=3)
        self.assertIn("round 3", text.splitlines()[0])


class RoundNumberingTest(unittest.TestCase):
    def _reports_dir(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: [f.unlink() for f in tmp.glob("*")] and tmp.rmdir())
        return tmp

    def test_next_round_number_starts_at_one_for_empty_dir(self):
        d = self._reports_dir()
        self.assertEqual(next_round_number(d), 1)

    def test_next_round_number_for_nonexistent_dir(self):
        self.assertEqual(next_round_number("/no/such/dir"), 1)

    def test_next_round_number_picks_up_existing_rounds(self):
        d = self._reports_dir()
        (d / "2026-09-01-rd-lead-cpp-israel-round1.md").write_text("x")
        (d / "2026-09-14-rd-lead-cpp-israel-round4.md").write_text("x")
        (d / "unrelated.md").write_text("x")
        self.assertEqual(next_round_number(d), 5)

    def test_default_report_path_uses_slug_and_round(self):
        d = self._reports_dir()
        path = default_report_path(d, 7)
        self.assertTrue(path.name.endswith("-rd-lead-cpp-israel-round7.md"))
        self.assertEqual(path.parent, d)


if __name__ == "__main__":
    unittest.main()
