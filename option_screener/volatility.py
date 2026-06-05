"""Historical stock data and volatility calculations."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from option_screener.clients import RateLimiter
from option_screener.config import ScreenerConfig

LOGGER = logging.getLogger(__name__)


def fetch_historical_bars(
    stock_client: object,
    symbols: list[str],
    config: ScreenerConfig,
    rate_limiter: RateLimiter,
) -> pd.DataFrame:
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame

    end_date = (datetime.now() - timedelta(days=1)).date()
    start_date = end_date - timedelta(days=config.historical_days)

    request = StockBarsRequest(
        symbol_or_symbols=symbols,
        timeframe=TimeFrame.Day,
        start=start_date,
        end=end_date,
    )
    LOGGER.info("Fetching historical bars from %s to %s", start_date, end_date)
    rate_limiter.wait()
    bars = stock_client.get_stock_bars(request)
    return bars.df


def clean_historical_bars(
    historical_bars: pd.DataFrame, min_records: int
) -> tuple[pd.DataFrame, list[str]]:
    record_count_by_ticker = historical_bars.groupby(level="symbol").size().sort_values()
    symbols_to_keep = record_count_by_ticker[record_count_by_ticker > min_records].index.tolist()
    clean = historical_bars.loc[
        historical_bars.index.get_level_values("symbol").isin(symbols_to_keep)
    ].reset_index()
    return clean, symbols_to_keep


def compute_historical_volatility(
    historical_bars: pd.DataFrame, trading_days: int = 252
) -> pd.DataFrame:
    def compute_hv(group: pd.DataFrame) -> float:
        prices = group["close"].dropna()
        log_returns = np.log(prices / prices.shift(1)).dropna()
        if len(log_returns) < 2:
            return np.nan
        return log_returns.std(ddof=0) * np.sqrt(trading_days)

    return (
        historical_bars.groupby("symbol")
        .apply(compute_hv)
        .reset_index(name="volatility")
    )


def _model_to_dict(model: object) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    return dict(model)


def fetch_latest_trades(
    stock_client: object,
    symbols: Iterable[str],
    rate_limiter: RateLimiter,
) -> pd.DataFrame:
    from alpaca.data.requests import StockLatestTradeRequest

    symbols = list(symbols)
    LOGGER.info("Fetching latest trades for %d symbols", len(symbols))
    rate_limiter.wait()
    response = stock_client.get_stock_latest_trade(
        StockLatestTradeRequest(symbol_or_symbols=symbols)
    )

    records = []
    for symbol, trade in response.items():
        record = _model_to_dict(trade)
        record.setdefault("symbol", symbol)
        records.append(record)

    df = pd.DataFrame(records)
    return df.rename(columns={"price": "underlying_price"})
