import pandas as pd
import pytest

from option_screener.screener import add_downside_stress_columns


def test_add_downside_stress_columns_for_cash_secured_put():
    df = pd.DataFrame(
        {
            "underlying_price": [100.0],
            "strike_price": [90.0],
            "contract_revenue": [100.0],
            "collateral": [9000.0],
        }
    )

    result = add_downside_stress_columns(df)

    assert result["pl_if_underlying_down_10_pct"].iloc[0] == 100.0
    assert result["return_if_underlying_down_10_pct"].iloc[0] == pytest.approx(
        100 / 9000
    )
    assert result["pl_if_underlying_down_20_pct"].iloc[0] == -900.0
    assert result["return_if_underlying_down_20_pct"].iloc[0] == pytest.approx(
        -900 / 9000
    )


def test_add_downside_stress_columns_handles_invalid_collateral():
    df = pd.DataFrame(
        {
            "underlying_price": [100.0],
            "strike_price": [90.0],
            "contract_revenue": [100.0],
            "collateral": [0.0],
        }
    )

    result = add_downside_stress_columns(df)

    assert pd.isna(result["return_if_underlying_down_10_pct"].iloc[0])
    assert pd.isna(result["return_if_underlying_down_20_pct"].iloc[0])
