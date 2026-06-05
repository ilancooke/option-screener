import pandas as pd
import pytest

from option_screener.screener import clean_final_output


def test_clean_final_output_formats_expiration_date_as_iso_string():
    df = pd.DataFrame(
        {
            "expiration_date": [pd.Timestamp("2026-07-17 00:00:00")],
            "bid_price": [0.25],
        }
    )

    result = clean_final_output(df)

    assert result["expiration_date"].iloc[0] == "2026-07-17"
    assert result["option_bid_price"].iloc[0] == 0.25


def test_clean_final_output_preserves_option_diagnostics():
    df = pd.DataFrame(
        {
            "expiration_date": [pd.Timestamp("2026-07-17")],
            "bid_price": [0.20],
            "ask_price": [0.30],
            "quote_timestamp": [pd.Timestamp.now(tz="UTC")],
            "bid_size": [4],
            "ask_size": [7],
            "trade_price": [0.25],
            "trade_size": [1],
            "daily_volume": [224],
            "daily_trade_count": [26],
            "daily_vwap": [0.245],
            "prev_daily_volume": [120],
            "prev_daily_trade_count": [14],
            "prev_daily_vwap": [0.220],
            "implied_volatility": [0.4567],
            "volatility": [0.3000],
            "delta": [-0.1234],
            "gamma": [0.0123],
            "theta": [-0.0456],
            "vega": [0.0789],
            "rho": [-0.01],
        }
    )

    result = clean_final_output(df)

    expected_columns = [
        "option_bid_price",
        "option_ask_price",
        "option_bid_ask_spread",
        "option_mid_price",
        "option_spread_pct",
        "quote_timestamp",
        "quote_age_minutes",
        "bid_size",
        "ask_size",
        "trade_price",
        "trade_size",
        "daily_volume",
        "daily_trade_count",
        "daily_vwap",
        "prev_daily_volume",
        "prev_daily_trade_count",
        "prev_daily_vwap",
        "implied_volatility",
        "historical_volatility",
        "iv_minus_hv",
        "iv_to_hv_ratio",
        "delta",
        "gamma",
        "theta",
        "vega",
        "rho",
    ]
    for column in expected_columns:
        assert column in result.columns

    assert result["option_bid_ask_spread"].iloc[0] == pytest.approx(0.10)
    assert result["option_mid_price"].iloc[0] == 0.25
    assert result["option_spread_pct"].iloc[0] == pytest.approx(0.4)
    assert result["quote_timestamp"].iloc[0]
    assert result["quote_age_minutes"].iloc[0] >= 0
    assert result["historical_volatility"].iloc[0] == 0.3000
    assert result["iv_minus_hv"].iloc[0] == pytest.approx(0.1567)
    assert result["iv_to_hv_ratio"].iloc[0] == pytest.approx(1.5223333333)


def test_clean_final_output_avoids_infinite_iv_to_hv_ratio():
    df = pd.DataFrame(
        {
            "expiration_date": [pd.Timestamp("2026-07-17")],
            "implied_volatility": [0.50],
            "volatility": [0.0],
        }
    )

    result = clean_final_output(df)

    assert pd.isna(result["iv_to_hv_ratio"].iloc[0])
