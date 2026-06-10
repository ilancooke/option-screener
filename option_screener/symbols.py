"""Symbol discovery and filtering."""

from __future__ import annotations

import logging

from option_screener.clients import RateLimiter
from option_screener.config import ScreenerConfig

LOGGER = logging.getLogger(__name__)


def get_optionable_active_listed_equity_symbols(
    trading_client: object, rate_limiter: RateLimiter
) -> list[str]:
    from alpaca.trading.enums import AssetClass, AssetExchange, AssetStatus
    from alpaca.trading.requests import GetAssetsRequest

    rate_limiter.wait()
    assets = trading_client.get_all_assets(
        GetAssetsRequest(
            asset_class=AssetClass.US_EQUITY,
            status=AssetStatus.ACTIVE,
            attributes="has_options",
        )
    )

    allowed_exchanges = {AssetExchange.NASDAQ, AssetExchange.NYSE}
    return sorted({
        asset.symbol
        for asset in assets
        if asset.exchange in allowed_exchanges
    })


def get_filtered_symbols(
    trading_client: object, config: ScreenerConfig, rate_limiter: RateLimiter
) -> list[str]:
    LOGGER.info("Loading active listed US equities with options from Alpaca")
    symbols = get_optionable_active_listed_equity_symbols(trading_client, rate_limiter)
    LOGGER.info("Loaded %d optionable active listed US equities", len(symbols))
    return symbols
