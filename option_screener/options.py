"""Option contract and option chain data."""

from __future__ import annotations

import logging
from collections.abc import Iterable

import pandas as pd

from option_screener.clients import RateLimiter
from option_screener.config import ScreenerConfig

LOGGER = logging.getLogger(__name__)

OPTION_CONTRACT_COLUMNS = [
    "symbol",
    "name",
    "underlying_symbol",
    "strike_price",
    "expiration_date",
    "close_price",
    "close_price_date",
    "open_interest",
    "open_interest_date",
    "style",
    "type",
    "status",
    "tradable",
    "size",
    "id",
]

OPTION_CHAIN_COLUMNS = [
    "option_symbol",
    "bid_price",
    "bid_size",
    "ask_price",
    "ask_size",
    "quote_timestamp",
    "trade_price",
    "trade_size",
    "trade_timestamp",
    "daily_volume",
    "daily_trade_count",
    "daily_vwap",
    "prev_daily_volume",
    "prev_daily_trade_count",
    "prev_daily_vwap",
    "implied_volatility",
    "delta",
    "gamma",
    "theta",
    "vega",
    "rho",
]


def _model_to_dict(model: object) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    return dict(model)


def _get_value(obj: object, attr_name: str, raw_key: str):
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(raw_key)
    return getattr(obj, attr_name, None)


def _get_snapshot_value(snapshot: object, attr_name: str, raw_key: str):
    return _get_value(snapshot, attr_name, raw_key)


def get_all_option_contracts(
    trading_client: object,
    underlying_symbols: list[str],
    config: ScreenerConfig,
    rate_limiter: RateLimiter,
) -> list[object]:
    from alpaca.trading.enums import AssetStatus
    from alpaca.trading.requests import GetOptionContractsRequest

    all_contracts = []
    page_token = None

    while True:
        request = GetOptionContractsRequest(
            underlying_symbols=underlying_symbols,
            status=AssetStatus.ACTIVE,
            expiration_date=config.expiration_date,
            type=config.option_type,
            limit=config.option_contract_page_limit,
            page_token=page_token,
        )
        rate_limiter.wait()
        response = trading_client.get_option_contracts(request)
        all_contracts.extend(response.option_contracts)
        LOGGER.info("Fetched %d option contracts so far", len(all_contracts))

        if response.next_page_token:
            page_token = response.next_page_token
        else:
            break

    return all_contracts


def filter_contracts_by_open_interest(
    contracts: Iterable[object], minimum_open_interest: int
) -> list[object]:
    return [
        contract
        for contract in contracts
        if contract.open_interest is not None and int(contract.open_interest) > minimum_open_interest
    ]


def flatten_option_contracts(option_list: Iterable[object]) -> pd.DataFrame:
    records = []

    for option in option_list:
        records.append(
            {
                "symbol": option.symbol,
                "name": option.name,
                "underlying_symbol": option.underlying_symbol,
                "strike_price": option.strike_price,
                "expiration_date": option.expiration_date,
                "close_price": float(option.close_price) if option.close_price else None,
                "close_price_date": option.close_price_date,
                "open_interest": int(option.open_interest) if option.open_interest else None,
                "open_interest_date": option.open_interest_date,
                "style": str(option.style.value) if option.style else None,
                "type": str(option.type.value) if option.type else None,
                "status": str(option.status.value) if option.status else None,
                "tradable": option.tradable,
                "size": int(option.size) if option.size else None,
                "id": str(option.id),
            }
        )

    return pd.DataFrame(records, columns=OPTION_CONTRACT_COLUMNS)


def option_symbols_from_contracts(contracts: Iterable[object]) -> list[str]:
    return [_model_to_dict(option)["symbol"] for option in contracts]


def fetch_option_chains(
    option_historical_data_client: object,
    underlying_symbols: list[str],
    config: ScreenerConfig,
    rate_limiter: RateLimiter,
) -> dict:
    from alpaca.data.requests import OptionChainRequest

    results = {}
    total = len(underlying_symbols)

    for index, symbol in enumerate(underlying_symbols, start=1):
        LOGGER.info("Fetching option chain %d/%d: %s", index, total, symbol)
        try:
            request = OptionChainRequest(
                underlying_symbol=symbol,
                type=config.option_type,
                expiration_date=config.expiration_date,
            )
            rate_limiter.wait()
            chain = option_historical_data_client.get_option_chain(request)
            LOGGER.info("Fetched %d option chain records for %s", len(chain.keys()), symbol)
            results.update(chain)
        except Exception:
            LOGGER.exception("Failed to get option chain for %s", symbol)

    return results


def flatten_option_chain(option_data: dict) -> pd.DataFrame:
    records = []

    for symbol, snapshot in option_data.items():
        quote = _get_snapshot_value(snapshot, "latest_quote", "latestQuote")
        trade = _get_snapshot_value(snapshot, "latest_trade", "latestTrade")
        greeks = _get_snapshot_value(snapshot, "greeks", "greeks")
        daily_bar = _get_snapshot_value(snapshot, "daily_bar", "dailyBar")
        prev_daily_bar = _get_snapshot_value(
            snapshot,
            "previous_daily_bar",
            "prevDailyBar",
        )

        records.append(
            {
                "option_symbol": symbol,
                "bid_price": _get_value(quote, "bid_price", "bp"),
                "bid_size": _get_value(quote, "bid_size", "bs"),
                "ask_price": _get_value(quote, "ask_price", "ap"),
                "ask_size": _get_value(quote, "ask_size", "as"),
                "quote_timestamp": _get_value(quote, "timestamp", "t"),
                "trade_price": _get_value(trade, "price", "p"),
                "trade_size": _get_value(trade, "size", "s"),
                "trade_timestamp": _get_value(trade, "timestamp", "t"),
                "daily_volume": _get_value(daily_bar, "volume", "v"),
                "daily_trade_count": _get_value(daily_bar, "trade_count", "n"),
                "daily_vwap": _get_value(daily_bar, "vwap", "vw"),
                "prev_daily_volume": _get_value(prev_daily_bar, "volume", "v"),
                "prev_daily_trade_count": (
                    _get_value(prev_daily_bar, "trade_count", "n")
                ),
                "prev_daily_vwap": _get_value(prev_daily_bar, "vwap", "vw"),
                "implied_volatility": _get_snapshot_value(
                    snapshot,
                    "implied_volatility",
                    "impliedVolatility",
                ),
                "delta": _get_value(greeks, "delta", "delta"),
                "gamma": _get_value(greeks, "gamma", "gamma"),
                "theta": _get_value(greeks, "theta", "theta"),
                "vega": _get_value(greeks, "vega", "vega"),
                "rho": _get_value(greeks, "rho", "rho"),
            }
        )

    return pd.DataFrame(records, columns=OPTION_CHAIN_COLUMNS)
