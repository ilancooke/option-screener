"""Probability calculations used by the screener."""

from __future__ import annotations

import math

import numpy as np
from scipy.stats import norm


def probability_put_expires_worthless(
    underlying_price: float,
    strike_price: float,
    time_till_expiry: float,
    risk_free_rate: float,
    volatility: float,
) -> float:
    if (
        underlying_price <= 0
        or strike_price <= 0
        or time_till_expiry <= 0
        or volatility <= 0
    ):
        return np.nan

    d2 = (
        math.log(underlying_price / strike_price)
        + (risk_free_rate - 0.5 * volatility**2) * time_till_expiry
    ) / (volatility * math.sqrt(time_till_expiry))
    return norm.cdf(d2)
