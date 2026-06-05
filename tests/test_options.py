from option_screener.options import (
    OPTION_CHAIN_COLUMNS,
    OPTION_CONTRACT_COLUMNS,
    flatten_option_chain,
    flatten_option_contracts,
)


def test_flatten_option_contracts_returns_schema_when_empty():
    result = flatten_option_contracts([])

    assert result.empty
    assert result.columns.tolist() == OPTION_CONTRACT_COLUMNS


def test_flatten_option_chain_returns_schema_when_empty():
    result = flatten_option_chain({})

    assert result.empty
    assert result.columns.tolist() == OPTION_CHAIN_COLUMNS
