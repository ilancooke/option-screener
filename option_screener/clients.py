"""Alpaca client construction and shared rate limiting."""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from threading import Lock

from option_screener.config import AlpacaCredentials, ScreenerConfig

LOGGER = logging.getLogger(__name__)


@dataclass
class RateLimiter:
    """Simple sliding-window limiter for API calls."""

    max_calls: int
    period_seconds: float = 60.0
    _calls: deque[float] = field(default_factory=deque, init=False)
    _lock: Lock = field(default_factory=Lock, init=False)

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            while self._calls and now - self._calls[0] >= self.period_seconds:
                self._calls.popleft()

            if len(self._calls) >= self.max_calls:
                sleep_for = self.period_seconds - (now - self._calls[0])
                if sleep_for > 0:
                    LOGGER.info("Rate limit reached; sleeping %.2f seconds", sleep_for)
                    time.sleep(sleep_for)
                now = time.monotonic()
                while self._calls and now - self._calls[0] >= self.period_seconds:
                    self._calls.popleft()

            self._calls.append(time.monotonic())


@dataclass(frozen=True)
class AlpacaClients:
    trading_client: object
    stock_client: object
    option_historical_data_client: object


def create_alpaca_clients(
    credentials: AlpacaCredentials, config: ScreenerConfig
) -> AlpacaClients:
    from alpaca.data.historical import OptionHistoricalDataClient, StockHistoricalDataClient
    from alpaca.trading.client import TradingClient

    return AlpacaClients(
        trading_client=TradingClient(
            credentials.api_key,
            credentials.secret_key,
            paper=config.paper_trading,
        ),
        stock_client=StockHistoricalDataClient(credentials.api_key, credentials.secret_key),
        option_historical_data_client=OptionHistoricalDataClient(
            credentials.api_key,
            credentials.secret_key,
            raw_data=True,
            url_override=None,
        ),
    )
