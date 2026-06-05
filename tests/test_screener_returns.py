import pandas as pd
import pytest

from option_screener.screener import add_return_columns


def test_add_return_columns_computes_annualized_return():
    df = pd.DataFrame(
        {
            "option_bid_price": [1.00],
            "strike_price": [100.0],
            "days_till_expiry": [30],
        }
    )

    result = add_return_columns(df)

    assert result["contract_revenue"].iloc[0] == 100
    assert result["collateral"].iloc[0] == 10_000
    assert result["potential_return"].iloc[0] == 0.01
    assert result["annualized_return"].iloc[0] == pytest.approx(0.1216666667)


def test_add_return_columns_avoids_annualizing_expired_contracts():
    df = pd.DataFrame(
        {
            "option_bid_price": [1.00],
            "strike_price": [100.0],
            "days_till_expiry": [0],
        }
    )

    result = add_return_columns(df)

    assert pd.isna(result["annualized_return"].iloc[0])
