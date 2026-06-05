from option_screener.screener import FINAL_OUTPUT_COLUMNS, empty_final_output


def test_empty_final_output_has_expected_columns():
    result = empty_final_output()

    assert result.empty
    assert result.columns.tolist() == FINAL_OUTPUT_COLUMNS
