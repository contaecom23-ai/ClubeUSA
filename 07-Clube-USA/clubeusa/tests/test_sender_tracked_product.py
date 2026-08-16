import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dealscanner2'))

def test_send_tracked_product_alert_includes_coupon_when_verified(mocker):
    from sender import send_tracked_product_alert

    mock_send = mocker.patch("sender._send_message")

    product = {"title": "Echo Dot (4th Gen)"}
    offer   = {"marketplace": "amazon", "price": 18.39, "url": "https://amazon.com/dp/B08N5WRWNW"}
    coupon  = {"code": "SAVE20ECHO", "verified": True}

    send_tracked_product_alert(product, offer, coupon, phone="+15551234567", lang="pt")

    mock_send.assert_called_once()
    sent_text = mock_send.call_args[0][1]
    assert "SAVE20ECHO" in sent_text
    assert "Echo Dot" in sent_text

def test_send_tracked_product_alert_omits_coupon_when_none(mocker):
    from sender import send_tracked_product_alert

    mock_send = mocker.patch("sender._send_message")

    product = {"title": "Echo Dot (4th Gen)"}
    offer   = {"marketplace": "amazon", "price": 18.39, "url": "https://amazon.com/dp/B08N5WRWNW"}

    send_tracked_product_alert(product, offer, None, phone="+15551234567", lang="pt")

    sent_text = mock_send.call_args[0][1]
    assert "Cupom" not in sent_text
