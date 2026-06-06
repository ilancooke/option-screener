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
    expiration_date: str | None = None
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
    output_path: Path = Path("output.xlsx")

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

    def validate(self) -> None:
        errors = []

        if not self.expiration_date:
            errors.append("expiration_date is required")
        if self.option_type not in {"put", "call"}:
            errors.append("option_type must be 'put' or 'call'")
        if not 0 <= self.risk_free_rate <= 1:
            errors.append("risk_free_rate must be between 0 and 1")
        if self.historical_days <= 0:
            errors.append("historical_days must be greater than 0")
        if self.trading_days <= 0:
            errors.append("trading_days must be greater than 0")
        if self.min_historical_records < 0:
            errors.append("min_historical_records must be greater than or equal to 0")
        if self.max_collateral <= 0:
            errors.append("max_collateral must be greater than 0")
        if not 0 <= self.min_probability <= 1:
            errors.append("min_probability must be between 0 and 1")
        if self.min_bid < 0:
            errors.append("min_bid must be greater than or equal to 0")
        if self.min_open_interest < 0:
            errors.append("min_open_interest must be greater than or equal to 0")
        if self.contract_open_interest_minimum < 0:
            errors.append(
                "contract_open_interest_minimum must be greater than or equal to 0"
            )
        if self.option_contract_page_limit <= 0:
            errors.append("option_contract_page_limit must be greater than 0")
        if self.max_api_calls_per_minute <= 0:
            errors.append("max_api_calls_per_minute must be greater than 0")
        if self.symbol_limit is not None and self.symbol_limit <= 0:
            errors.append("symbol_limit must be greater than 0 when provided")
        if not self.options_url:
            errors.append("options_url is required")

        if errors:
            raise ValueError("Invalid screener config: " + "; ".join(errors))


def _coerce_config_values(values: dict[str, Any]) -> dict[str, Any]:
    coerced = dict(values)
    if "output_path" in coerced and coerced["output_path"] is not None:
        coerced["output_path"] = Path(coerced["output_path"])
    return coerced
