import pandas as pd

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
