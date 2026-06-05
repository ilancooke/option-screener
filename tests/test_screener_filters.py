import pandas as pd

from option_screener.config import ScreenerConfig
from option_screener.screener import apply_filters


def test_apply_filters_keeps_best_candidate_per_underlying():
    config = ScreenerConfig(
        min_probability=0.70,
        max_collateral=15_000,
        min_bid=0.10,
        min_open_interest=100,
    )
    df = pd.DataFrame(
        [
            {
                "underlying_symbol": "AAA",
                "prob_put_expires_worthless": 0.80,
                "collateral": 10_000,
                "option_bid_price": 0.20,
                "open_interest": 150,
                "potential_return": 0.002,
            },
            {
                "underlying_symbol": "AAA",
                "prob_put_expires_worthless": 0.82,
                "collateral": 9_500,
                "option_bid_price": 0.30,
                "open_interest": 200,
                "potential_return": 0.003,
            },
            {
                "underlying_symbol": "BBB",
                "prob_put_expires_worthless": 0.60,
                "collateral": 8_000,
                "option_bid_price": 0.40,
                "open_interest": 300,
                "potential_return": 0.005,
            },
        ]
    )

    result = apply_filters(df, config)

    assert result["underlying_symbol"].tolist() == ["AAA"]
    assert result["potential_return"].iloc[0] == 0.003
