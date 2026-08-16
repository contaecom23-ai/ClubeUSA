import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dealscanner2'))

from unittest.mock import MagicMock, patch

def _fake_entry(title, summary):
    e = MagicMock()
    e.title = title
    e.summary = summary
    return e

def test_find_candidates_extracts_code_from_title_and_summary(mocker):
    from coupon_finder import find_candidates

    fake_feed = MagicMock()
    fake_feed.entries = [
        _fake_entry(
            "Amazon: 20% off Echo Dot with code SAVE20ECHO",
            "Use coupon code SAVE20ECHO at checkout for 20% off.",
        ),
        _fake_entry("Unrelated deal about shoes", "no code here"),
    ]
    mocker.patch("coupon_finder.feedparser.parse", return_value=fake_feed)

    candidates = find_candidates("Echo Dot", "amazon")

    assert len(candidates) == 1
    assert candidates[0]["code"] == "SAVE20ECHO"
    assert candidates[0]["source"] == "slickdeals"

def test_find_candidates_returns_empty_when_no_match(mocker):
    from coupon_finder import find_candidates

    fake_feed = MagicMock()
    fake_feed.entries = [_fake_entry("Totally unrelated deal", "no code")]
    mocker.patch("coupon_finder.feedparser.parse", return_value=fake_feed)

    candidates = find_candidates("Echo Dot", "amazon")
    assert candidates == []

def test_find_candidates_handles_feed_error_gracefully(mocker):
    from coupon_finder import find_candidates

    mocker.patch("coupon_finder.feedparser.parse", side_effect=Exception("timeout"))

    candidates = find_candidates("Echo Dot", "amazon")
    assert candidates == []
