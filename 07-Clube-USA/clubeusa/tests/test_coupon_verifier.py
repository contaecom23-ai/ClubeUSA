# clubeusa/tests/test_coupon_verifier.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dealscanner2'))

from unittest.mock import patch

def test_verify_returns_none_for_unsupported_marketplace():
    from coupon_verifier import verify
    result = verify("walmart", "CODE123", "https://walmart.com/ip/1")
    assert result is None

def test_verify_returns_true_when_amazon_driver_confirms(mocker):
    from coupon_verifier import verify
    mocker.patch("coupon_verifier._verify_amazon", return_value=True)
    result = verify("amazon", "SAVE20ECHO", "https://amazon.com/dp/B08N5WRWNW")
    assert result is True

def test_verify_returns_none_when_amazon_driver_raises(mocker):
    from coupon_verifier import verify
    mocker.patch("coupon_verifier._verify_amazon", side_effect=Exception("timeout no playwright"))
    result = verify("amazon", "SAVE20ECHO", "https://amazon.com/dp/B08N5WRWNW")
    assert result is None

def test_verify_amazon_driver_detects_price_drop():
    from coupon_verifier import _verify_amazon

    class FakePage:
        def __init__(self):
            self.calls = []
        def goto(self, url, **kw): self.calls.append(("goto", url))
        def click(self, sel, **kw): self.calls.append(("click", sel))
        def fill(self, sel, value, **kw): self.calls.append(("fill", sel, value))
        def wait_for_selector(self, sel, **kw): self.calls.append(("wait", sel))
        def text_content(self, sel):
            # primeira leitura = total antes do cupom, segunda = depois
            self._reads = getattr(self, "_reads", 0) + 1
            return "$22.99" if self._reads == 1 else "$18.39"

    class FakeContext:
        def new_page(self): return FakePage()
        def close(self): pass

    class FakeBrowser:
        def new_context(self): return FakeContext()
        def close(self): pass

    class FakeChromium:
        def launch(self, **kw): return FakeBrowser()

    class FakePlaywright:
        chromium = FakeChromium()
        def __enter__(self): return self
        def __exit__(self, *a): pass

    with patch("coupon_verifier.sync_playwright", return_value=FakePlaywright()):
        result = _verify_amazon("SAVE20ECHO", "https://amazon.com/dp/B08N5WRWNW")

    assert result is True
