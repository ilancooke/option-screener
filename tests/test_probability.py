import math

from option_screener.probability import probability_put_expires_worthless


def test_probability_put_expires_worthless_returns_reasonable_value():
    probability = probability_put_expires_worthless(
        underlying_price=100,
        strike_price=90,
        time_till_expiry=30 / 365,
        risk_free_rate=0.0435,
        volatility=0.25,
    )

    assert 0.0 < probability < 1.0
    assert probability > 0.8


def test_probability_put_expires_worthless_rejects_invalid_inputs():
    probability = probability_put_expires_worthless(
        underlying_price=100,
        strike_price=90,
        time_till_expiry=0,
        risk_free_rate=0.0435,
        volatility=0.25,
    )

    assert math.isnan(probability)
