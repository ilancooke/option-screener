from option_screener.options import (
    OPTION_CHAIN_COLUMNS,
    OPTION_CONTRACT_COLUMNS,
    flatten_option_chain,
    flatten_option_contracts,
)


class FakeBar:
    def __init__(self, volume, trade_count, vwap):
        self.volume = volume
        self.trade_count = trade_count
        self.vwap = vwap


class FakeSnapshot:
    latest_quote = None
    latest_trade = None
    greeks = None
    implied_volatility = None

    def __init__(self):
        self.daily_bar = FakeBar(volume=224, trade_count=26, vwap=0.245)
        self.previous_daily_bar = FakeBar(volume=120, trade_count=14, vwap=0.220)


def test_flatten_option_contracts_returns_schema_when_empty():
    result = flatten_option_contracts([])

    assert result.empty
    assert result.columns.tolist() == OPTION_CONTRACT_COLUMNS


def test_flatten_option_chain_returns_schema_when_empty():
    result = flatten_option_chain({})

    assert result.empty
    assert result.columns.tolist() == OPTION_CHAIN_COLUMNS


def test_flatten_option_chain_extracts_daily_volume_diagnostics():
    result = flatten_option_chain({"AAA260717P00090000": FakeSnapshot()})

    row = result.iloc[0]

    assert row["daily_volume"] == 224
    assert row["daily_trade_count"] == 26
    assert row["daily_vwap"] == 0.245
    assert row["prev_daily_volume"] == 120
    assert row["prev_daily_trade_count"] == 14
    assert row["prev_daily_vwap"] == 0.220


def test_flatten_option_chain_extracts_raw_snapshot_data():
    result = flatten_option_chain(
        {
            "AAA260717P00090000": {
                "latestQuote": {
                    "bp": 0.20,
                    "bs": 4,
                    "ap": 0.30,
                    "as": 7,
                    "t": "2026-06-05T15:30:00Z",
                },
                "latestTrade": {
                    "p": 0.25,
                    "s": 1,
                    "t": "2026-06-05T15:29:00Z",
                },
                "dailyBar": {
                    "v": 224,
                    "n": 26,
                    "vw": 0.245,
                },
                "prevDailyBar": {
                    "v": 120,
                    "n": 14,
                    "vw": 0.220,
                },
                "impliedVolatility": 0.4567,
                "greeks": {
                    "delta": -0.1234,
                    "gamma": 0.0123,
                    "theta": -0.0456,
                    "vega": 0.0789,
                    "rho": -0.01,
                },
            }
        }
    )

    row = result.iloc[0]

    assert row["bid_price"] == 0.20
    assert row["ask_price"] == 0.30
    assert row["quote_timestamp"] == "2026-06-05T15:30:00Z"
    assert row["trade_price"] == 0.25
    assert row["daily_volume"] == 224
    assert row["prev_daily_volume"] == 120
    assert row["implied_volatility"] == 0.4567
    assert row["delta"] == -0.1234
