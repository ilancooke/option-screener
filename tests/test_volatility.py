import numpy as np
import pandas as pd

from option_screener.volatility import compute_historical_volatility


def test_compute_historical_volatility_per_symbol():
    df = pd.DataFrame(
        {
            "symbol": ["AAA", "AAA", "AAA", "BBB", "BBB", "BBB"],
            "close": [100.0, 101.0, 103.0, 50.0, 49.0, 51.0],
        }
    )

    result = compute_historical_volatility(df, trading_days=252)
    aaa_vol = result.loc[result["symbol"] == "AAA", "volatility"].iloc[0]

    returns = np.log(pd.Series([100.0, 101.0, 103.0]) / pd.Series([100.0, 101.0, 103.0]).shift(1)).dropna()
    expected = returns.std(ddof=0) * np.sqrt(252)

    assert np.isclose(aaa_vol, expected)
