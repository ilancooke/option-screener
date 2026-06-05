"""Symbol discovery and filtering."""

from __future__ import annotations

import logging
from collections.abc import Iterable

import pandas as pd

from option_screener.clients import RateLimiter
from option_screener.config import ScreenerConfig

LOGGER = logging.getLogger(__name__)


def load_optionable_symbols(options_url: str) -> list[str]:
    options_df = pd.read_csv(options_url, sep="|", skipfooter=1, engine="python")
    symbols = options_df["Underlying Symbol"].dropna().unique().tolist()
    return sorted(symbols)


def get_active_listed_equity_symbols(trading_client: object, rate_limiter: RateLimiter) -> set[str]:
    from alpaca.trading.enums import AssetClass, AssetExchange
    from alpaca.trading.requests import GetAssetsRequest

    rate_limiter.wait()
    assets = trading_client.get_all_assets(
        GetAssetsRequest(asset_class=AssetClass.US_EQUITY, status="active")
    )

    allowed_exchanges = {AssetExchange.NASDAQ, AssetExchange.NYSE, AssetExchange.AMEX}
    return {
        asset.symbol
        for asset in assets
        if asset.exchange in allowed_exchanges
    }


def filter_optionable_equities(
    optionable_symbols: Iterable[str], valid_equity_symbols: Iterable[str]
) -> list[str]:
    return sorted(set(optionable_symbols) & set(valid_equity_symbols))


def get_filtered_symbols(
    trading_client: object, config: ScreenerConfig, rate_limiter: RateLimiter
) -> list[str]:
    LOGGER.info("Loading optionable symbols")
    optionable_symbols = load_optionable_symbols(config.options_url)
    LOGGER.info("Loaded %d optionable symbols", len(optionable_symbols))

    LOGGER.info("Loading active listed US equities from Alpaca")
    valid_equity_symbols = get_active_listed_equity_symbols(trading_client, rate_limiter)
    LOGGER.info("Loaded %d active listed US equities", len(valid_equity_symbols))

    filtered_symbols = filter_optionable_equities(optionable_symbols, valid_equity_symbols)
    LOGGER.info("Kept %d optionable active listed equities", len(filtered_symbols))
    return filtered_symbols
