import pandas as pd

from option_screener.screener import (
    FINAL_OUTPUT_COLUMNS,
    empty_final_output,
    order_output_columns,
)


def test_empty_final_output_has_expected_columns():
    result = empty_final_output()

    assert result.empty
    assert result.columns.tolist() == FINAL_OUTPUT_COLUMNS


def test_order_output_columns_uses_final_schema_and_appends_extras():
    df = pd.DataFrame(
        {
            "rho": [0.1],
            "underlying_symbol": ["AAA"],
            "extra": ["kept"],
            "option_symbol": ["AAA260717P00090000"],
        }
    )

    result = order_output_columns(df)

    assert result.columns.tolist() == [
        "underlying_symbol",
        "option_symbol",
        "rho",
        "extra",
    ]
