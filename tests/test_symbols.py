from option_screener.symbols import get_optionable_active_listed_equity_symbols


class FakeExchange:
    NASDAQ = "NASDAQ"
    NYSE = "NYSE"
    AMEX = "AMEX"
    ARCA = "ARCA"


class FakeAsset:
    def __init__(self, symbol, exchange):
        self.symbol = symbol
        self.exchange = exchange


class FakeTradingClient:
    def __init__(self, assets):
        self.assets = assets
        self.request = None

    def get_all_assets(self, request):
        self.request = request
        return self.assets


class FakeRateLimiter:
    def __init__(self):
        self.wait_count = 0

    def wait(self):
        self.wait_count += 1


def test_get_optionable_active_listed_equity_symbols_filters_exchange(monkeypatch):
    monkeypatch.setattr(
        "alpaca.trading.enums.AssetExchange",
        FakeExchange,
    )
    assets = [
        FakeAsset("MSFT", FakeExchange.NASDAQ),
        FakeAsset("AAPL", FakeExchange.NASDAQ),
        FakeAsset("IBM", FakeExchange.NYSE),
        FakeAsset("BTG", FakeExchange.AMEX),
        FakeAsset("SPY", FakeExchange.ARCA),
    ]
    trading_client = FakeTradingClient(assets)
    rate_limiter = FakeRateLimiter()

    result = get_optionable_active_listed_equity_symbols(trading_client, rate_limiter)

    assert result == ["AAPL", "IBM", "MSFT"]
    assert rate_limiter.wait_count == 1
    assert trading_client.request.attributes == "has_options"
