import sys
from unittest.mock import MagicMock

if "aiohttp" not in sys.modules:
    sys.modules["aiohttp"] = MagicMock()

if "feedparser" not in sys.modules:
    class MockFeed:
        def __init__(self, entries):
            self.entries = entries

    def mock_parse(raw_xml):
        if not raw_xml:
            return MockFeed([])
        return MockFeed([
            {
                "title": "Test Title",
                "link": "https://example.com/news/1",
                "summary": "Test Summary Description",
            }
        ])
    mock_feedparser = MagicMock()
    mock_feedparser.parse = mock_parse
    sys.modules["feedparser"] = mock_feedparser

from app.parser import NewsParser


def test_parse_feed_empty():
    res = NewsParser.parse_feed("")
    assert res == []


def test_parse_feed_entries():
    sample_rss = "<rss><channel><item><title>Test Title</title></item></channel></rss>"
    res = NewsParser.parse_feed(sample_rss)
    assert len(res) == 1
    assert res[0]["title"] == "Test Title"
    assert res[0]["link"] == "https://example.com/news/1"