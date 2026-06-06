#!/usr/bin/env python3
"""Run the option screener from the command line."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from option_screener.config import AlpacaCredentials, ScreenerConfig
from option_screener.screener import run_screener

DEFAULT_CONFIG_PATH = Path("config/strategy.yaml")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Screen cash-secured put candidates.")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Strategy config file. Defaults to config/strategy.yaml.",
    )
    parser.add_argument("--expiration-date")
    parser.add_argument("--option-type")
    parser.add_argument("--risk-free-rate", type=float)
    parser.add_argument("--historical-days", type=int)
    parser.add_argument("--max-collateral", type=float)
    parser.add_argument("--min-probability", type=float)
    parser.add_argument("--min-bid", type=float)
    parser.add_argument("--min-open-interest", type=int)
    parser.add_argument(
        "--max-api-calls-per-minute",
        type=int,
    )
    parser.add_argument(
        "--symbol-limit",
        type=int,
        help="Limit the number of filtered symbols processed; useful for smoke tests.",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--live-trading", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_dotenv()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    config = ScreenerConfig.from_yaml(args.config)
    config = config.with_overrides(
        expiration_date=args.expiration_date,
        option_type=args.option_type,
        risk_free_rate=args.risk_free_rate,
        historical_days=args.historical_days,
        max_collateral=args.max_collateral,
        min_probability=args.min_probability,
        min_bid=args.min_bid,
        min_open_interest=args.min_open_interest,
        max_api_calls_per_minute=args.max_api_calls_per_minute,
        symbol_limit=args.symbol_limit,
        output_path=args.output,
        paper_trading=False if args.live_trading else None,
    )
    try:
        config.validate()
    except ValueError as error:
        raise SystemExit(f"Configuration error: {error}") from error
    credentials = AlpacaCredentials.from_env()
    run_screener(credentials, config)


if __name__ == "__main__":
    main()
