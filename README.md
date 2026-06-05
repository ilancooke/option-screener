# option-screener

Prototype-to-package conversion of a cash-secured put option screener using Alpaca market data.

The original exploratory workflow lives in `prototype/alpaca.ipynb`. The package version keeps the same core methodology and default filters while moving credentials, configuration, rate limiting, and output into ordinary Python modules.

## Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Set Alpaca credentials in your environment:

```bash
export ALPACA_API_KEY=...
export ALPACA_SECRET_KEY=...
```

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
- 4.35% risk-free rate
- 70% minimum estimated probability of expiring worthless
- $15,000 maximum collateral
- $0.10 minimum bid
- 100 minimum open interest
- 180 Alpaca API calls per minute

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

- The current probability calculation intentionally matches the prototype and uses historical volatility.
- See `ROADMAP.md` for planned methodology improvements.
