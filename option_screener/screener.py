"""End-to-end option screening pipeline."""

from __future__ import annotations

import logging
from datetime import datetime

import numpy as np
import pandas as pd

from option_screener.clients import RateLimiter, create_alpaca_clients
from option_screener.config import AlpacaCredentials, ScreenerConfig
from option_screener.options import (
    fetch_option_chains,
    filter_contracts_by_open_interest,
    flatten_option_chain,
    flatten_option_contracts,
    get_all_option_contracts,
    option_symbols_from_contracts,
)
from option_screener.output import write_excel
from option_screener.probability import probability_put_expires_worthless
from option_screener.symbols import get_filtered_symbols
from option_screener.volatility import (
    clean_historical_bars,
    compute_historical_volatility,
    fetch_historical_bars,
    fetch_latest_trades,
)

LOGGER = logging.getLogger(__name__)

FINAL_OUTPUT_COLUMNS = [
    "name",
    "underlying_symbol",
    "strike_price",
    "expiration_date",
    "open_interest",
    "type",
    "option_symbol",
    "option_bid_price",
    "option_ask_price",
    "option_bid_ask_spread",
    "option_mid_price",
    "option_spread_pct",
    "quote_timestamp",
    "quote_age_minutes",
    "bid_size",
    "ask_size",
    "trade_price",
    "trade_size",
    "daily_volume",
    "daily_trade_count",
    "daily_vwap",
    "prev_daily_volume",
    "prev_daily_trade_count",
    "prev_daily_vwap",
    "implied_volatility",
    "historical_volatility",
    "iv_minus_hv",
    "iv_to_hv_ratio",
    "delta",
    "gamma",
    "theta",
    "vega",
    "rho",
    "underlying_price",
    "dollar_out_of_the_money",
    "percent_out_of_the_money",
    "days_till_expiry",
    "prob_put_expires_worthless",
    "contract_revenue",
    "collateral",
    "potential_return",
    "annualized_return",
]


def empty_final_output() -> pd.DataFrame:
    return pd.DataFrame(columns=FINAL_OUTPUT_COLUMNS)


def assemble_screener_data(
    option_contracts: pd.DataFrame,
    option_chain: pd.DataFrame,
    latest_trades: pd.DataFrame,
    historical_volatility: pd.DataFrame,
    config: ScreenerConfig,
) -> pd.DataFrame:
    merged = pd.merge(
        pd.merge(
            pd.merge(
                option_contracts,
                option_chain,
                left_on="symbol",
                right_on="option_symbol",
                how="inner",
            ),
            latest_trades,
            left_on="underlying_symbol",
            right_on="symbol",
            how="inner",
            suffixes=("", "_latest"),
        ),
        historical_volatility,
        left_on="underlying_symbol",
        right_on="symbol",
        how="inner",
        suffixes=("", "_latest_2"),
    )

    merged["expiration_date"] = pd.to_datetime(merged["expiration_date"])
    today = pd.Timestamp(datetime.today().date())
    merged["days_till_expiry"] = (merged["expiration_date"] - today).dt.days
    merged["time_till_expiry"] = merged["days_till_expiry"] / 365
    merged["risk_free_rate"] = config.risk_free_rate

    merged["prob_put_expires_worthless"] = merged.apply(
        lambda row: probability_put_expires_worthless(
            row["underlying_price"],
            row["strike_price"],
            row["time_till_expiry"],
            row["risk_free_rate"],
            row["implied_volatility"],
        ),
        axis=1,
    )

    return merged


def clean_final_output(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    cols_to_drop = [
        "open_interest_date",
        "style",
        "tradable",
        "status",
        "size",
        "id",
        "symbol",
        "trade_timestamp",
        "ticker",
        "symbol_latest",
        "timestamp",
        "exchange",
        "size_latest",
        "id_latest",
        "conditions",
        "tape",
        "symbol_latest_2",
        "time_till_expiry",
        "risk_free_rate",
        "close_price",
        "close_price_date",
    ]
    output.drop(columns=cols_to_drop, inplace=True, errors="ignore")
    output.rename(
        columns={
            "bid_price": "option_bid_price",
            "ask_price": "option_ask_price",
            "volatility": "historical_volatility",
        },
        inplace=True,
    )
    if {"option_bid_price", "option_ask_price"}.issubset(output.columns):
        output["option_bid_ask_spread"] = (
            output["option_ask_price"] - output["option_bid_price"]
        )
        output["option_mid_price"] = (
            output["option_ask_price"] + output["option_bid_price"]
        ) / 2
        output["option_spread_pct"] = (
            output["option_bid_ask_spread"] / output["option_mid_price"]
        )
    if {"implied_volatility", "historical_volatility"}.issubset(output.columns):
        output["iv_minus_hv"] = (
            output["implied_volatility"] - output["historical_volatility"]
        )
        output["iv_to_hv_ratio"] = (
            output["implied_volatility"] / output["historical_volatility"]
        )
        output.loc[output["historical_volatility"] <= 0, "iv_to_hv_ratio"] = pd.NA
    if "quote_timestamp" in output.columns:
        quote_timestamps = pd.to_datetime(output["quote_timestamp"], utc=True, errors="coerce")
        now = pd.Timestamp.now(tz="UTC")
        output["quote_age_minutes"] = (
            (now - quote_timestamps).dt.total_seconds() / 60
        )
        output["quote_timestamp"] = quote_timestamps.dt.strftime("%Y-%m-%d %H:%M:%S%z")
    if "expiration_date" in output.columns:
        output["expiration_date"] = pd.to_datetime(output["expiration_date"]).dt.strftime("%Y-%m-%d")
    return output


def add_return_columns(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    output["contract_revenue"] = output["option_bid_price"] * 100
    output["collateral"] = output["strike_price"] * 100
    output["potential_return"] = output["contract_revenue"] / output["collateral"]
    output["annualized_return"] = pd.NA
    valid_days = output["days_till_expiry"] > 0
    output.loc[valid_days, "annualized_return"] = (
        output.loc[valid_days, "potential_return"]
        * 365
        / output.loc[valid_days, "days_till_expiry"]
    )
    return output


def add_moneyness_columns(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    output["dollar_out_of_the_money"] = (
        output["underlying_price"] - output["strike_price"]
    )
    output["percent_out_of_the_money"] = (
        output["dollar_out_of_the_money"] / output["underlying_price"]
    )
    output.loc[output["underlying_price"] <= 0, "percent_out_of_the_money"] = pd.NA
    return output


def round_output_columns(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    round_cols_2 = [
        "strike_price",
        "close_price",
        "bid_price",
        "option_bid_price",
        "option_ask_price",
        "option_bid_ask_spread",
        "option_mid_price",
        "trade_price",
        "daily_vwap",
        "prev_daily_vwap",
        "underlying_price",
        "dollar_out_of_the_money",
        "contract_revenue",
        "collateral",
    ]
    round_cols_4 = [
        "implied_volatility",
        "delta",
        "gamma",
        "theta",
        "vega",
        "rho",
        "historical_volatility",
        "iv_minus_hv",
        "iv_to_hv_ratio",
        "option_spread_pct",
        "quote_age_minutes",
        "percent_out_of_the_money",
        "prob_put_expires_worthless",
        "potential_return",
        "annualized_return",
    ]
    cols_2 = [col for col in round_cols_2 if col in output.columns]
    cols_4 = [col for col in round_cols_4 if col in output.columns]
    output[cols_2] = output[cols_2].round(2)
    output[cols_4] = output[cols_4].round(4)
    return output


def apply_filters(df: pd.DataFrame, config: ScreenerConfig) -> pd.DataFrame:
    filtered = df.copy()
    implied_volatility = pd.to_numeric(filtered["implied_volatility"], errors="coerce")
    filtered = filtered[
        implied_volatility.notna()
        & np.isfinite(implied_volatility)
        & (implied_volatility > 0)
    ]
    filtered = filtered[filtered["prob_put_expires_worthless"] > config.min_probability]
    filtered = filtered[filtered["collateral"] <= config.max_collateral]
    filtered = filtered[filtered["option_bid_price"] > config.min_bid]
    filtered = filtered[filtered["open_interest"] >= config.min_open_interest]
    return (
        filtered.sort_values("potential_return", ascending=False)
        .drop_duplicates(subset="underlying_symbol", keep="first")
        .reset_index(drop=True)
    )


def build_screen(credentials: AlpacaCredentials, config: ScreenerConfig) -> pd.DataFrame:
    clients = create_alpaca_clients(credentials, config)
    rate_limiter = RateLimiter(max_calls=config.max_api_calls_per_minute)

    filtered_symbols = get_filtered_symbols(
        clients.trading_client, config=config, rate_limiter=rate_limiter
    )
    if config.symbol_limit is not None:
        filtered_symbols = filtered_symbols[: config.symbol_limit]
        LOGGER.info("Applied symbol limit; using %d symbols", len(filtered_symbols))

    historical_bars = fetch_historical_bars(
        clients.stock_client,
        filtered_symbols,
        config=config,
        rate_limiter=rate_limiter,
    )
    clean_bars, symbols_to_keep = clean_historical_bars(
        historical_bars,
        min_records=config.min_historical_records,
    )
    LOGGER.info("Kept %d symbols with sufficient historical records", len(symbols_to_keep))

    historical_volatility = compute_historical_volatility(
        clean_bars,
        trading_days=config.trading_days,
    )
    latest_trades = fetch_latest_trades(
        clients.stock_client,
        symbols_to_keep,
        rate_limiter=rate_limiter,
    )

    contracts = get_all_option_contracts(
        clients.trading_client,
        symbols_to_keep,
        config=config,
        rate_limiter=rate_limiter,
    )
    open_interest_contracts = filter_contracts_by_open_interest(
        contracts,
        minimum_open_interest=config.contract_open_interest_minimum,
    )
    if not open_interest_contracts:
        LOGGER.warning("No option contracts passed the open-interest prefilter")
        return empty_final_output()

    option_symbols = option_symbols_from_contracts(open_interest_contracts)

    option_contracts = flatten_option_contracts(open_interest_contracts)
    option_contracts = option_contracts[option_contracts["tradable"] == True]
    if option_contracts.empty:
        LOGGER.warning("No tradable option contracts found")
        return empty_final_output()

    option_chain_results = fetch_option_chains(
        clients.option_historical_data_client,
        symbols_to_keep,
        config=config,
        rate_limiter=rate_limiter,
    )
    option_chain = flatten_option_chain(option_chain_results)
    if option_chain.empty:
        LOGGER.warning("No option chain records found")
        return empty_final_output()

    option_chain["ticker"] = option_chain["option_symbol"].str.extract(r"^([A-Z]+)")
    option_chain = option_chain[
        option_chain["option_symbol"].isin(option_symbols)
    ].reset_index(drop=True)
    if option_chain.empty:
        LOGGER.warning("No option chain records matched tradable option contracts")
        return empty_final_output()

    merged = assemble_screener_data(
        option_contracts=option_contracts,
        option_chain=option_chain,
        latest_trades=latest_trades,
        historical_volatility=historical_volatility,
        config=config,
    )
    output = clean_final_output(merged)
    output = add_moneyness_columns(output)
    output = add_return_columns(output)
    output = round_output_columns(output)
    output = apply_filters(output, config)
    LOGGER.info("Final screen has %d rows", len(output))
    return output


def run_screener(credentials: AlpacaCredentials, config: ScreenerConfig) -> pd.DataFrame:
    df = build_screen(credentials, config)
    write_excel(df, config.output_path)
    LOGGER.info("Wrote %s", config.output_path)
    return df
