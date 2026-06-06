import pandas as pd
import pytest

from option_screener.screener import add_scenario_expected_value_columns


def test_add_scenario_expected_value_columns():
    df = pd.DataFrame(
        {
            "prob_put_expires_worthless": [0.80],
            "contract_revenue": [100.0],
            "collateral": [9000.0],
            "pl_if_underlying_down_10_pct": [100.0],
            "pl_if_underlying_down_20_pct": [-900.0],
        }
    )

    result = add_scenario_expected_value_columns(df)

    assert result["scenario_ev_down_10_pct"].iloc[0] == 100.0
    assert result["scenario_ev_return_down_10_pct"].iloc[0] == pytest.approx(
        100 / 9000
    )
    assert result["scenario_ev_down_20_pct"].iloc[0] == pytest.approx(-100.0)
    assert result["scenario_ev_return_down_20_pct"].iloc[0] == pytest.approx(
        -100 / 9000
    )


def test_add_scenario_expected_value_columns_handles_invalid_collateral():
    df = pd.DataFrame(
        {
            "prob_put_expires_worthless": [0.80],
            "contract_revenue": [100.0],
            "collateral": [0.0],
            "pl_if_underlying_down_10_pct": [100.0],
            "pl_if_underlying_down_20_pct": [-900.0],
        }
    )

    result = add_scenario_expected_value_columns(df)

    assert pd.isna(result["scenario_ev_return_down_10_pct"].iloc[0])
    assert pd.isna(result["scenario_ev_return_down_20_pct"].iloc[0])
