"""The real-price anchor: deflate a nominal price history to today's dollars by CPI."""

from assay.commodities.realprice import real_price_anchor


def test_deflates_to_today_dollars_and_averages():
    cpi = [("2000-06-01", 100.0), ("2026-06-01", 200.0)]
    prices = [("2000-06-01", 50.0), ("2026-06-01", 80.0)]
    a = real_price_anchor(prices, cpi, min_obs=2)
    # 2000 deflates 50 * (200/100) = 100; 2026 stays 80 at the latest CPI; average is 90.
    assert a is not None
    assert abs(a.avg - 90.0) < 1e-9
    assert a.n == 2
    assert a.span == "2000-2026"


def test_unit_factor_converts_the_price():
    cpi = [("2026-06-01", 200.0), ("2026-07-01", 200.0)]
    prices = [("2026-06-01", 2204.62), ("2026-07-01", 2204.62)]  # USD per metric ton
    a = real_price_anchor(prices, cpi, unit_factor=1.0 / 2204.62, min_obs=2)
    assert abs(a.avg - 1.0) < 1e-6  # converted to USD per pound


def test_none_when_too_little_data():
    assert real_price_anchor([("2026-01-01", 50.0)], [("2026-01-01", 100.0)], min_obs=24) is None
