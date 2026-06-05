import pandas as pd
import pytest

from option_screener.screener import add_moneyness_columns


def test_add_moneyness_columns_for_put_candidate():
    df = pd.DataFrame(
        {
            "underlying_price": [100.0],
            "strike_price": [90.0],
        }
    )

    result = add_moneyness_columns(df)

    assert "strike_to_underlying" not in result.columns
    assert result["dollar_out_of_the_money"].iloc[0] == 10.0
    assert result["percent_out_of_the_money"].iloc[0] == 0.1


def test_add_moneyness_columns_handles_invalid_underlying_price():
    df = pd.DataFrame(
        {
            "underlying_price": [0.0],
            "strike_price": [90.0],
        }
    )

    result = add_moneyness_columns(df)

    assert "strike_to_underlying" not in result.columns
    assert result["dollar_out_of_the_money"].iloc[0] == -90.0
    assert pd.isna(result["percent_out_of_the_money"].iloc[0])
