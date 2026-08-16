import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dealscanner2'))

from unittest.mock import patch, MagicMock

def test_get_item_by_asin_returns_item_on_200():
    from amazon_api import get_item_by_asin

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "ItemsResult": {"Items": [{"ASIN": "B08N5WRWNW", "ItemInfo": {"Title": {"DisplayValue": "Echo Dot"}}}]}
    }
    with patch("amazon_api.requests.post", return_value=mock_resp):
        item, err = get_item_by_asin("AK", "SK", "tag-20", "B08N5WRWNW")

    assert err is None
    assert item["ASIN"] == "B08N5WRWNW"

def test_get_item_by_asin_returns_error_on_404():
    from amazon_api import get_item_by_asin

    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.json.return_value = {"Errors": [{"Message": "Item nao encontrado"}]}
    with patch("amazon_api.requests.post", return_value=mock_resp):
        item, err = get_item_by_asin("AK", "SK", "tag-20", "B00000000X")

    assert item is None
    assert "nao encontrado" in err
