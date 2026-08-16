import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dealscanner2'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import MagicMock

def test_check_tracked_products_updates_price_and_refreshes_coupons(mocker):
    from scheduler import check_tracked_products

    mocker.patch("scheduler.config.SUPABASE_URL", "https://example.supabase.co")
    mocker.patch("scheduler.config.SUPABASE_SERVICE_KEY", "fake-key")

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"id": "tp-1", "title": "Echo Dot", "source": "amazon", "source_id": "B08N5WRWNW"},
    ]
    mocker.patch("scheduler._supabase", return_value=mock_sb)
    mocker.patch(
        "scheduler.fetch_source_details",
        return_value={"title": "Echo Dot", "price": 19.99, "image_url": None, "url": "https://amazon.com/dp/B08N5WRWNW"},
    )
    mocker.patch("scheduler.find_offers", return_value=[])
    mock_refresh = mocker.patch("scheduler.refresh_coupons")

    check_tracked_products()

    mock_refresh.assert_called_once_with("tp-1")
    mock_sb.table().upsert.assert_called()

def test_check_tracked_products_skips_product_on_error(mocker):
    from scheduler import check_tracked_products

    mocker.patch("scheduler.config.SUPABASE_URL", "https://example.supabase.co")
    mocker.patch("scheduler.config.SUPABASE_SERVICE_KEY", "fake-key")

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"id": "tp-1", "title": "Echo Dot", "source": "amazon", "source_id": "B08N5WRWNW"},
        {"id": "tp-2", "title": "Air Fryer", "source": "walmart", "source_id": "114215867"},
    ]
    mocker.patch("scheduler._supabase", return_value=mock_sb)
    mocker.patch("scheduler.fetch_source_details", side_effect=[Exception("API fora do ar"), {
        "title": "Air Fryer", "price": 59.0, "image_url": None, "url": "https://walmart.com/ip/1",
    }])
    mocker.patch("scheduler.find_offers", return_value=[])
    mock_refresh = mocker.patch("scheduler.refresh_coupons")

    check_tracked_products()

    # tp-1 falhou mas tp-2 ainda deve ter sido processado
    mock_refresh.assert_called_once_with("tp-2")
