"""The monetary lens: where a metal's price sits versus its own real-price and money-supply history."""

from assay.commodities.monetary import monetary_lens


def test_lens_places_spot_at_top_of_a_rising_history():
    # Rising price, flat CPI and M2: a spot above all history sits at the 100th percentile.
    cpi = [(f"{2000 + y}-01-01", 100.0) for y in range(27)]
    m2 = [(f"{2000 + y}-01-01", 1000.0) for y in range(27)]
    prices = [(f"{2000 + y}-01-01", float(y + 1)) for y in range(27)]  # 1..27
    lens = monetary_lens(prices, cpi, m2, spot_value=100.0, min_obs=12)
    assert lens is not None
    assert lens.real_pct == 100.0  # 100 is above every deflated historical price
    assert lens.m2_pct == 100.0
    assert lens.real_span == "2000-2026"


def test_lens_none_when_too_little_history():
    assert (
        monetary_lens(
            [("2026-01-01", 1.0)],
            [("2026-01-01", 100.0)],
            [("2026-01-01", 1000.0)],
            1.0,
            min_obs=60,
        )
        is None
    )
