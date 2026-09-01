import unittest
from unittest import mock

from job_matcher.sources import greenhouse, lever, remoteok


def _mock_response(json_data, status=200):
    resp = mock.Mock()
    resp.status_code = status
    resp.json.return_value = json_data
    resp.raise_for_status = mock.Mock()
    if status >= 400:
        resp.raise_for_status.side_effect = Exception(f"HTTP {status}")
    return resp


class GreenhouseSourceTest(unittest.TestCase):
    @mock.patch("job_matcher.sources.greenhouse.requests.get")
    def test_fetch_jobs_normalizes_fields(self, mock_get):
        mock_get.return_value = _mock_response(
            {
                "jobs": [
                    {
                        "id": 123,
                        "title": "Backend Engineer",
                        "absolute_url": "https://example.com/123",
                        "location": {"name": "Remote - US"},
                        "departments": [{"name": "Engineering"}],
                        "content": "<p>Requirements</p><ul><li>Python</li></ul>",
                        "updated_at": "2026-01-01",
                    }
                ]
            }
        )

        jobs = greenhouse.fetch_jobs("acme")

        self.assertEqual(len(jobs), 1)
        job = jobs[0]
        self.assertEqual(job.id, "123")
        self.assertEqual(job.title, "Backend Engineer")
        self.assertEqual(job.company, "acme")
        self.assertEqual(job.source, "greenhouse")
        self.assertTrue(job.remote)
        self.assertIn("Python", job.description)
        self.assertEqual(job.department, "Engineering")

    @mock.patch("job_matcher.sources.greenhouse.requests.get")
    def test_fetch_jobs_handles_missing_location(self, mock_get):
        mock_get.return_value = _mock_response(
            {"jobs": [{"id": 1, "title": "X", "content": ""}]}
        )
        jobs = greenhouse.fetch_jobs("acme")
        self.assertEqual(jobs[0].location, "")
        self.assertIsNone(jobs[0].remote)


class LeverSourceTest(unittest.TestCase):
    @mock.patch("job_matcher.sources.lever.requests.get")
    def test_fetch_jobs_normalizes_fields(self, mock_get):
        mock_get.return_value = _mock_response(
            [
                {
                    "id": "abc",
                    "text": "Staff Engineer",
                    "hostedUrl": "https://jobs.lever.co/acme/abc",
                    "categories": {"location": "Remote", "team": "Platform"},
                    "descriptionHtml": "<p>About us</p>",
                    "lists": [
                        {"text": "Requirements", "content": "<ul><li>Go</li></ul>"}
                    ],
                    "createdAt": 1700000000,
                }
            ]
        )

        jobs = lever.fetch_jobs("acme")

        self.assertEqual(len(jobs), 1)
        job = jobs[0]
        self.assertEqual(job.title, "Staff Engineer")
        self.assertEqual(job.source, "lever")
        self.assertTrue(job.remote)
        self.assertIn("Go", job.description)
        self.assertIn("Requirements", job.description)


class RemoteOkSourceTest(unittest.TestCase):
    @mock.patch("job_matcher.sources.remoteok.requests.get")
    def test_fetch_jobs_skips_legal_row_and_filters_by_tag(self, mock_get):
        mock_get.return_value = _mock_response(
            [
                {"legal": "notice"},
                {
                    "id": "1",
                    "position": "Backend Engineer",
                    "company": "Acme",
                    "url": "https://remoteok.com/1",
                    "tags": ["backend", "python"],
                    "description": "<p>desc</p>",
                    "location": "Worldwide",
                    "date": "2026-01-01",
                },
                {
                    "id": "2",
                    "position": "Sales Manager",
                    "company": "Acme",
                    "url": "https://remoteok.com/2",
                    "tags": ["sales"],
                    "description": "<p>desc</p>",
                    "location": "Worldwide",
                    "date": "2026-01-01",
                },
            ]
        )

        jobs = remoteok.fetch_jobs(tags=["backend"])

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].title, "Backend Engineer")
        self.assertTrue(jobs[0].remote)

    @mock.patch("job_matcher.sources.remoteok.requests.get")
    def test_fetch_jobs_no_filter_returns_all(self, mock_get):
        mock_get.return_value = _mock_response(
            [
                {"legal": "notice"},
                {"id": "1", "position": "A", "tags": [], "description": ""},
                {"id": "2", "position": "B", "tags": [], "description": ""},
            ]
        )
        jobs = remoteok.fetch_jobs()
        self.assertEqual(len(jobs), 2)


if __name__ == "__main__":
    unittest.main()
