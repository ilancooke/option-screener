"""Configuration for the option screener."""

from __future__ import annotations

import os
from dataclasses import dataclass
from dataclasses import fields
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class AlpacaCredentials:
    api_key: str
    secret_key: str

    @classmethod
    def from_env(cls) -> "AlpacaCredentials":
        api_key = os.environ.get("ALPACA_API_KEY")
        secret_key = os.environ.get("ALPACA_SECRET_KEY") or os.environ.get("ALPACA_SECRET")

        missing = []
        if not api_key:
            missing.append("ALPACA_API_KEY")
        if not secret_key:
            missing.append("ALPACA_SECRET_KEY")
        if missing:
            raise RuntimeError(
                "Missing Alpaca credentials. Set " + ", ".join(missing) + " in the environment."
            )

        return cls(api_key=api_key, secret_key=secret_key)


@dataclass(frozen=True)
class ScreenerConfig:
    expiration_date: str = "2025-08-15"
    option_type: str = "put"
    risk_free_rate: float = 0.0435
    historical_days: int = 90
    trading_days: int = 252
    min_historical_records: int = 57

    max_collateral: float = 15_000
    min_probability: float = 0.70
    min_bid: float = 0.10
    min_open_interest: int = 100
    contract_open_interest_minimum: int = 0

    option_contract_page_limit: int = 10_000
    max_api_calls_per_minute: int = 180
    symbol_limit: int | None = None
    paper_trading: bool = True

    options_url: str = "https://www.nasdaqtrader.com/dynamic/SymDir/options.txt"
    output_path: Path = Path("output20250815.xlsx")

    @classmethod
    def from_yaml(cls, path: Path) -> "ScreenerConfig":
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}

        if not isinstance(data, dict):
            raise ValueError(f"Config file must contain a mapping: {path}")

        valid_fields = {field.name for field in fields(cls)}
        unknown_keys = sorted(set(data) - valid_fields)
        if unknown_keys:
            raise ValueError(
                f"Unknown config keys in {path}: " + ", ".join(unknown_keys)
            )

        return cls(**_coerce_config_values(data))

    def with_overrides(self, **overrides: Any) -> "ScreenerConfig":
        values = {field.name: getattr(self, field.name) for field in fields(self)}
        values.update({key: value for key, value in overrides.items() if value is not None})
        return type(self)(**_coerce_config_values(values))


def _coerce_config_values(values: dict[str, Any]) -> dict[str, Any]:
    coerced = dict(values)
    if "output_path" in coerced and coerced["output_path"] is not None:
        coerced["output_path"] = Path(coerced["output_path"])
    return coerced
