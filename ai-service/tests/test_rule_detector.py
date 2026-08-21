import unittest

from rule_detector import extract_endpoint_changes


class EndpointExtractionTests(unittest.TestCase):
    def test_markdown_notice_extracts_deprecated_and_announced_endpoints(self) -> None:
        body = """Deprecated endpoints
- GET /domains/{domain}
- GET /keywords/{keyword}/overview

New v3 endpoints
- POST /v3/shorten/bulk
- GET /v3/shorten/{shortlink}
"""
        deprecated, announced = extract_endpoint_changes("U301 API Update", body)
        self.assertEqual([("GET", "/domains/{domain}"), ("GET", "/keywords/{keyword}/overview")], [(x.method, x.path) for x in deprecated])
        self.assertEqual([("POST", "/v3/shorten/bulk"), ("GET", "/v3/shorten/{shortlink}")], [(x.method, x.path) for x in announced])

    def test_plain_text_notice_without_newlines_is_parsed(self) -> None:
        body = "Some existing requests:GET /domains/{domain}GET /keywords/search The latest API resources are now available under the /v3/shorten namespace. POST /v3/shorten/bulk GET /v3/shorten/list"
        deprecated, announced = extract_endpoint_changes("Action required", body)
        self.assertEqual([("GET", "/domains/{domain}"), ("GET", "/keywords/search")], [(x.method, x.path) for x in deprecated])
        self.assertEqual([("POST", "/v3/shorten/bulk"), ("GET", "/v3/shorten/list")], [(x.method, x.path) for x in announced])
