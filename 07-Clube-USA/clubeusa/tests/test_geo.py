"""
tests/test_geo.py — Testes unitarios para utils/geo.py (Fase 1.2)

Sem dependencias externas: nao chama Nominatim, nao usa banco.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.geo import is_valid_us_zip, haversine_miles, filter_deals_by_radius


class TestIsValidUsZip:
    def test_valid(self):
        assert is_valid_us_zip("33101") is True
        assert is_valid_us_zip("10001") is True
        assert is_valid_us_zip("00501") is True

    def test_too_short(self):
        assert is_valid_us_zip("3310") is False

    def test_too_long(self):
        assert is_valid_us_zip("331011") is False

    def test_letters(self):
        assert is_valid_us_zip("3310A") is False

    def test_empty(self):
        assert is_valid_us_zip("") is False

    def test_none(self):
        assert is_valid_us_zip(None) is False


class TestHaversineMiles:
    def test_same_point(self):
        assert haversine_miles(25.77, -80.19, 25.77, -80.19) == pytest.approx(0.0, abs=0.001)

    def test_miami_to_miami_beach(self):
        # Miami downtown -> Miami Beach ~5.5 milhas
        dist = haversine_miles(25.7617, -80.1918, 25.7907, -80.1300)
        assert 4.0 < dist < 7.0

    def test_ny_to_la(self):
        # NY -> LA ~2451 milhas
        dist = haversine_miles(40.7128, -74.0060, 34.0522, -118.2437)
        assert 2400 < dist < 2500

    def test_symmetric(self):
        d1 = haversine_miles(25.0, -80.0, 26.0, -81.0)
        d2 = haversine_miles(26.0, -81.0, 25.0, -80.0)
        assert d1 == pytest.approx(d2, rel=1e-6)


class TestFilterDealsByRadius:
    MIAMI_LAT = 25.7617
    MIAMI_LNG = -80.1918

    def _deal(self, is_local=False, lat=None, lng=None, **kwargs):
        base = {"id": "1", "title": "Test", "is_local": is_local, "lat": lat, "lng": lng}
        base.update(kwargs)
        return base

    def test_online_deal_always_passes(self):
        deal = self._deal(is_local=False)
        result = filter_deals_by_radius([deal], self.MIAMI_LAT, self.MIAMI_LNG, 5.0)
        assert len(result) == 1

    def test_local_deal_in_radius_passes(self):
        # Miami Beach: ~4.5 milhas do centro
        deal = self._deal(is_local=True, lat=25.7907, lng=-80.1300)
        result = filter_deals_by_radius([deal], self.MIAMI_LAT, self.MIAMI_LNG, 10.0)
        assert len(result) == 1
        assert "_distance_miles" in result[0]

    def test_local_deal_outside_radius_filtered(self):
        # Orlando: ~230 milhas de Miami
        deal = self._deal(is_local=True, lat=28.5383, lng=-81.3792)
        result = filter_deals_by_radius([deal], self.MIAMI_LAT, self.MIAMI_LNG, 5.0)
        assert len(result) == 0

    def test_local_deal_no_coords_passes(self):
        deal = self._deal(is_local=True, lat=None, lng=None)
        result = filter_deals_by_radius([deal], self.MIAMI_LAT, self.MIAMI_LNG, 5.0)
        assert len(result) == 1

    def test_mixed_deals(self):
        online = self._deal(is_local=False, id="online")
        nearby = self._deal(is_local=True, lat=25.79, lng=-80.13, id="nearby")
        far = self._deal(is_local=True, lat=28.54, lng=-81.38, id="far")
        result = filter_deals_by_radius([online, nearby, far], self.MIAMI_LAT, self.MIAMI_LNG, 10.0)
        ids = {d["id"] for d in result}
        assert "online" in ids
        assert "nearby" in ids
        assert "far" not in ids

    def test_distance_annotation(self):
        deal = self._deal(is_local=True, lat=25.7907, lng=-80.1300)
        result = filter_deals_by_radius([deal], self.MIAMI_LAT, self.MIAMI_LNG, 10.0)
        assert result[0]["_distance_miles"] > 0

    def test_original_deal_not_mutated(self):
        deal = self._deal(is_local=True, lat=25.7907, lng=-80.1300)
        filter_deals_by_radius([deal], self.MIAMI_LAT, self.MIAMI_LNG, 10.0)
        assert "_distance_miles" not in deal
