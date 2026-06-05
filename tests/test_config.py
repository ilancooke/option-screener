from pathlib import Path

import pytest

from option_screener.config import ScreenerConfig


def test_screener_config_loads_from_yaml(tmp_path):
    config_path = tmp_path / "strategy.yaml"
    config_path.write_text(
        """
option_type: put
historical_days: 45
max_collateral: 5000
output_path: output-test.xlsx
""",
        encoding="utf-8",
    )

    config = ScreenerConfig.from_yaml(config_path)

    assert config.option_type == "put"
    assert config.historical_days == 45
    assert config.max_collateral == 5000
    assert config.output_path == Path("output-test.xlsx")


def test_screener_config_rejects_unknown_yaml_keys(tmp_path):
    config_path = tmp_path / "strategy.yaml"
    config_path.write_text("not_a_real_key: 123\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Unknown config keys"):
        ScreenerConfig.from_yaml(config_path)


def test_screener_config_with_overrides_ignores_none_values():
    config = ScreenerConfig(historical_days=90, expiration_date="2026-07-17")

    updated = config.with_overrides(historical_days=None, expiration_date="2026-08-21")

    assert updated.historical_days == 90
    assert updated.expiration_date == "2026-08-21"
