from unittest.mock import MagicMock

MAX = 10

def test_create_tracked_product_raises_on_limit(mocker):
    from services.tracked_product_service import create_tracked_product
    mock_sb = MagicMock()
    mock_sb.table().select().eq().eq().execute.return_value.data = [{}] * MAX
    mocker.patch("services.tracked_product_service._supabase", return_value=mock_sb)

    import pytest
    with pytest.raises(ValueError, match="Limite"):
        create_tracked_product("m-1", "https://www.amazon.com/dp/B08N5WRWNW")

def test_create_tracked_product_success(mocker):
    from services.tracked_product_service import create_tracked_product

    mock_sb = MagicMock()
    mock_sb.table().select().eq().eq().execute.return_value.data = []  # sem limite
    mock_sb.table().insert().execute.return_value.data = [{
        "id": "tp-1", "member_id": "m-1", "source": "amazon",
        "source_id": "B08N5WRWNW", "title": "Echo Dot", "status": "active",
    }]
    mocker.patch("services.tracked_product_service._supabase", return_value=mock_sb)
    mocker.patch(
        "services.tracked_product_service.identify_source",
        return_value=("amazon", "B08N5WRWNW"),
    )
    mocker.patch(
        "services.tracked_product_service.fetch_source_details",
        return_value={"title": "Echo Dot", "price": 22.99, "image_url": None, "url": "https://amazon.com/dp/B08N5WRWNW"},
    )
    mocker.patch(
        "services.tracked_product_service.find_offers",
        return_value=[{"marketplace": "walmart", "price": 24.5, "url": "https://walmart.com/ip/1"}],
    )
    mocker.patch("services.tracked_product_service._trigger_coupon_refresh_async")

    result = create_tracked_product("m-1", "https://www.amazon.com/dp/B08N5WRWNW")

    assert result["id"] == "tp-1"
    assert result["title"] == "Echo Dot"
    assert result["offers"][0]["marketplace"] == "amazon"
    assert result["offers"][1]["marketplace"] == "walmart"

def test_create_tracked_product_wraps_matcher_error(mocker):
    from services.tracked_product_service import create_tracked_product

    mock_sb = MagicMock()
    mock_sb.table().select().eq().eq().execute.return_value.data = []
    mocker.patch("services.tracked_product_service._supabase", return_value=mock_sb)
    mocker.patch(
        "services.tracked_product_service.identify_source",
        side_effect=ValueError("Link não reconhecido."),
    )

    import pytest
    with pytest.raises(ValueError, match="não reconhecido"):
        create_tracked_product("m-1", "https://google.com")

def test_create_tracked_product_rolls_back_on_offers_upsert_failure(mocker):
    from services.tracked_product_service import create_tracked_product
    import pytest

    mock_sb = MagicMock()
    mock_sb.table().select().eq().eq().execute.return_value.data = []  # sem limite
    mock_sb.table().insert().execute.return_value.data = [{
        "id": "tp-1", "member_id": "m-1", "source": "amazon",
        "source_id": "B08N5WRWNW", "title": "Echo Dot", "status": "active",
    }]
    mock_sb.table().upsert().execute.side_effect = Exception("upsert falhou")
    mocker.patch("services.tracked_product_service._supabase", return_value=mock_sb)
    mocker.patch(
        "services.tracked_product_service.identify_source",
        return_value=("amazon", "B08N5WRWNW"),
    )
    mocker.patch(
        "services.tracked_product_service.fetch_source_details",
        return_value={"title": "Echo Dot", "price": 22.99, "image_url": None, "url": "https://amazon.com/dp/B08N5WRWNW"},
    )
    mocker.patch(
        "services.tracked_product_service.find_offers",
        return_value=[{"marketplace": "walmart", "price": 24.5, "url": "https://walmart.com/ip/1"}],
    )
    mock_trigger = mocker.patch("services.tracked_product_service._trigger_coupon_refresh_async")

    with pytest.raises(ValueError, match="ofertas"):
        create_tracked_product("m-1", "https://www.amazon.com/dp/B08N5WRWNW")

    mock_sb.table().delete().eq.assert_any_call("id", "tp-1")
    mock_trigger.assert_not_called()


def test_create_tracked_product_raises_when_insert_returns_no_data(mocker):
    from services.tracked_product_service import create_tracked_product
    import pytest

    mock_sb = MagicMock()
    mock_sb.table().select().eq().eq().execute.return_value.data = []
    mock_sb.table().insert().execute.return_value.data = []
    mocker.patch("services.tracked_product_service._supabase", return_value=mock_sb)
    mocker.patch(
        "services.tracked_product_service.identify_source",
        return_value=("amazon", "B08N5WRWNW"),
    )
    mocker.patch(
        "services.tracked_product_service.fetch_source_details",
        return_value={"title": "Echo Dot", "price": 22.99, "image_url": None, "url": "https://amazon.com/dp/B08N5WRWNW"},
    )

    with pytest.raises(ValueError, match="Não foi possível criar"):
        create_tracked_product("m-1", "https://www.amazon.com/dp/B08N5WRWNW")


def test_cancel_tracked_product_returns_true(mocker):
    from services.tracked_product_service import cancel_tracked_product
    mock_sb = MagicMock()
    mock_sb.table().update().eq().eq().execute.return_value.data = [{"id": "tp-1"}]
    mocker.patch("services.tracked_product_service._supabase", return_value=mock_sb)

    assert cancel_tracked_product("tp-1", "m-1") is True

def test_cancel_tracked_product_not_found_returns_false(mocker):
    from services.tracked_product_service import cancel_tracked_product
    mock_sb = MagicMock()
    mock_sb.table().update().eq().eq().execute.return_value.data = []
    mocker.patch("services.tracked_product_service._supabase", return_value=mock_sb)

    assert cancel_tracked_product("tp-nao-existe", "m-1") is False

def test_refresh_coupons_writes_verified_and_unverified(mocker):
    from services.tracked_product_service import refresh_coupons

    mock_sb = MagicMock()
    product_result = MagicMock(data=[{"id": "tp-1", "title": "Echo Dot"}])
    offers_result = MagicMock(data=[
        {"marketplace": "amazon", "url": "https://amazon.com/dp/B08N5WRWNW"},
        {"marketplace": "walmart", "url": "https://walmart.com/ip/1"},
    ])
    mock_sb.table().select().eq().execute.side_effect = [product_result, offers_result]
    mocker.patch("services.tracked_product_service._supabase", return_value=mock_sb)
    mocker.patch(
        "services.tracked_product_service.find_candidates",
        side_effect=[
            [{"code": "SAVE20", "description": "20% off", "source": "slickdeals"}],
            [],
        ],
    )
    mocker.patch("services.tracked_product_service.verify", return_value=True)

    refresh_coupons("tp-1")

    mock_sb.table().upsert.assert_called()


def test_refresh_coupons_returns_without_raising_when_product_missing(mocker):
    from services.tracked_product_service import refresh_coupons

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = []
    mocker.patch("services.tracked_product_service._supabase", return_value=mock_sb)
    mock_find_candidates = mocker.patch("services.tracked_product_service.find_candidates")
    mock_verify = mocker.patch("services.tracked_product_service.verify")

    refresh_coupons("tp-nao-existe")

    mock_find_candidates.assert_not_called()
    mock_verify.assert_not_called()
