import pandas as pd
import pytest

from option_screener.config import ScreenerConfig
from option_screener.probability import probability_put_expires_worthless
from option_screener.screener import assemble_screener_data


def test_assemble_screener_data_uses_iv_for_primary_probability():
    config = ScreenerConfig(risk_free_rate=0.0435)
    option_contracts = pd.DataFrame(
        {
            "symbol": ["AAA260717P00090000"],
            "underlying_symbol": ["AAA"],
            "strike_price": [90.0],
            "expiration_date": [pd.Timestamp("2026-07-17")],
        }
    )
    option_chain = pd.DataFrame(
        {
            "option_symbol": ["AAA260717P00090000"],
            "implied_volatility": [0.45],
        }
    )
    latest_trades = pd.DataFrame(
        {
            "symbol": ["AAA"],
            "underlying_price": [100.0],
        }
    )
    historical_volatility = pd.DataFrame(
        {
            "symbol": ["AAA"],
            "volatility": [0.20],
        }
    )

    result = assemble_screener_data(
        option_contracts=option_contracts,
        option_chain=option_chain,
        latest_trades=latest_trades,
        historical_volatility=historical_volatility,
        config=config,
    )
    row = result.iloc[0]

    expected_iv_probability = probability_put_expires_worthless(
        row["underlying_price"],
        row["strike_price"],
        row["time_till_expiry"],
        row["risk_free_rate"],
        row["implied_volatility"],
    )
    hv_probability = probability_put_expires_worthless(
        row["underlying_price"],
        row["strike_price"],
        row["time_till_expiry"],
        row["risk_free_rate"],
        row["volatility"],
    )

    assert row["prob_put_expires_worthless"] == pytest.approx(expected_iv_probability)
    assert row["prob_put_expires_worthless"] != pytest.approx(hv_probability)
