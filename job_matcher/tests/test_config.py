import os
import tempfile
import unittest
from pathlib import Path

from job_matcher.config import Profile, SourcesConfig


class SourcesConfigTest(unittest.TestCase):
    def _write(self, content: str) -> Path:
        fd, name = tempfile.mkstemp(suffix=".yaml")
        os.close(fd)  # avoid a lingering handle blocking cleanup on Windows
        tmp = Path(name)
        tmp.write_text(content, encoding="utf-8")
        self.addCleanup(tmp.unlink)
        return tmp

    def test_keyword_filter_keeps_matching_titles(self):
        path = self._write("keywords: [backend, platform]\n")
        cfg = SourcesConfig.load(path)
        self.assertTrue(cfg.title_matches_keywords("Senior Backend Engineer"))
        self.assertFalse(cfg.title_matches_keywords("Sales Manager"))

    def test_no_keywords_keeps_everything(self):
        path = self._write("greenhouse_boards: [acme]\n")
        cfg = SourcesConfig.load(path)
        self.assertTrue(cfg.title_matches_keywords("Anything at all"))

    def test_exclude_keywords_override_keyword_match(self):
        path = self._write(
            "keywords: [engineer]\nexclude_keywords: [intern]\n"
        )
        cfg = SourcesConfig.load(path)
        self.assertFalse(cfg.title_matches_keywords("Engineering Intern"))
        self.assertTrue(cfg.title_matches_keywords("Backend Engineer"))

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            SourcesConfig.load("does-not-exist.yaml")


class ProfileTest(unittest.TestCase):
    def test_as_prompt_text_renders_yaml(self):
        profile = Profile(raw={"background": {"skills": ["Python"]}})
        text = profile.as_prompt_text()
        self.assertIn("Python", text)
        self.assertIn("background", text)


if __name__ == "__main__":
    unittest.main()
