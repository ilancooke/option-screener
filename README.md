# option-screener

Cash-secured put option screener using Alpaca market data.

The original exploratory workflow lives in `prototype/alpaca.ipynb`. The production path is the Python package and CLI in `option_screener/` and `scripts/run_screener.py`.

## Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Set Alpaca credentials in `.env` or in your shell environment:

```text
ALPACA_API_KEY=...
ALPACA_SECRET_KEY=...
```

The CLI automatically loads `.env`. Existing shell environment variables take precedence.

## Run

```bash
python3 scripts/run_screener.py \
  --expiration-date 2026-07-17 \
  --output output.xlsx
```

For a smaller live smoke test:

```bash
python3 scripts/run_screener.py \
  --expiration-date 2026-07-17 \
  --symbol-limit 100 \
  --output output-smoke.xlsx
```

Stable strategy defaults live in `config/strategy.yaml`:

- put options
- 90 calendar days of historical prices
- 3.71% risk-free rate
- 70% minimum estimated probability of expiring worthless
- $20,000 maximum collateral
- $0.10 minimum bid
- 100 minimum open interest
- 180 Alpaca API calls per minute

`option_screener/config.py` defines the config schema and fallback defaults.
`config/strategy.yaml` is the documented strategy configuration for this project.

The screener universe comes from Alpaca's Assets API using the `has_options` attribute, filtered to active US equities on NASDAQ or NYSE.

Per-run values are usually passed through the CLI:

- `--expiration-date`
- `--output`
- `--symbol-limit`
- `--log-level`

To use a different strategy config:

```bash
python3 scripts/run_screener.py \
  --config config/strategy.yaml \
  --expiration-date 2026-07-17 \
  --output output.xlsx
```

## Notes

- The primary probability calculation uses option implied volatility. Historical volatility is preserved for comparison.
- Contracts with missing, non-finite, zero, or negative implied volatility are excluded from the final screen.
- The output includes diagnostics for bid/ask spread, quote age, option volume, Greeks, IV/HV comparison, moneyness, annualized return, downside stress, and scenario EV.
- When multiple contracts pass for the same underlying, the screener currently keeps the highest `potential_return` contract.
- See `ROADMAP.md` for planned methodology improvements.
