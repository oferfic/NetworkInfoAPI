import json
import unittest
from unittest import mock

from job_matcher.config import Profile
from job_matcher.matcher import Matcher, _parse_json_response
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
        description="Requirements: Python, 5+ years experience.",
    )
    defaults.update(overrides)
    return JobPosting(**defaults)


def _text_response(payload: dict):
    block = mock.Mock()
    block.type = "text"
    block.text = json.dumps(payload)
    resp = mock.Mock()
    resp.content = [block]
    return resp


class ParseJsonResponseTest(unittest.TestCase):
    def test_plain_json(self):
        data = _parse_json_response('{"score": 80, "verdict": "strong_fit"}')
        self.assertEqual(data["score"], 80)

    def test_json_wrapped_in_markdown_fence(self):
        text = '```json\n{"score": 50}\n```'
        data = _parse_json_response(text)
        self.assertEqual(data["score"], 50)

    def test_json_with_surrounding_prose(self):
        text = 'Here you go:\n{"score": 10, "verdict": "not_fit"}\nThanks!'
        data = _parse_json_response(text)
        self.assertEqual(data["score"], 10)

    def test_unparseable_returns_none(self):
        self.assertIsNone(_parse_json_response("not json at all"))


class MatcherTest(unittest.TestCase):
    def setUp(self):
        self.profile = Profile(raw={"background": {"skills": ["Python"]}})

    @mock.patch("job_matcher.matcher.anthropic.Anthropic")
    def test_evaluate_parses_successful_response(self, mock_anthropic_cls):
        mock_client = mock.Mock()
        mock_client.messages.create.return_value = _text_response(
            {
                "score": 82,
                "verdict": "strong_fit",
                "matched_requirements": ["Python"],
                "missing_requirements": [],
                "preference_notes": ["Remote matches preference"],
                "reasoning": "Good match.",
            }
        )
        mock_anthropic_cls.return_value = mock_client

        matcher = Matcher(self.profile, api_key="test-key")
        result = matcher.evaluate(_job())

        self.assertTrue(result.ok)
        self.assertEqual(result.score, 82)
        self.assertEqual(result.verdict, "strong_fit")
        self.assertEqual(result.matched_requirements, ["Python"])
        mock_client.messages.create.assert_called_once()

    @mock.patch("job_matcher.matcher.anthropic.Anthropic")
    def test_evaluate_handles_api_error(self, mock_anthropic_cls):
        mock_client = mock.Mock()
        mock_client.messages.create.side_effect = RuntimeError("boom")
        mock_anthropic_cls.return_value = mock_client

        matcher = Matcher(self.profile, api_key="test-key")
        result = matcher.evaluate(_job())

        self.assertFalse(result.ok)
        self.assertEqual(result.score, 0)
        self.assertIn("boom", result.error)

    @mock.patch("job_matcher.matcher.anthropic.Anthropic")
    def test_evaluate_handles_unparseable_response(self, mock_anthropic_cls):
        mock_client = mock.Mock()
        mock_client.messages.create.return_value = _text_response(None)
        # Force truly unparseable text instead of "null"
        mock_client.messages.create.return_value.content[0].text = "not json"
        mock_anthropic_cls.return_value = mock_client

        matcher = Matcher(self.profile, api_key="test-key")
        result = matcher.evaluate(_job())

        self.assertFalse(result.ok)
        self.assertEqual(result.verdict, "error")

    def test_missing_api_key_raises(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(RuntimeError):
                Matcher(self.profile)


if __name__ == "__main__":
    unittest.main()
