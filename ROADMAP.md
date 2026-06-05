# Option Screener Roadmap

This repo currently contains a prototype notebook for exploring cash-secured put candidates. The notebook is useful as a candidate generator, but the methodology should be tightened before the output is treated as a trading strategy.

## Completed Improvements

- Preserve Greeks and option diagnostics in the output.
   Keep delta, theta, vega, implied volatility, bid, ask, spread, and volume in the final table instead of dropping them.

- Compare implied volatility against historical volatility.
   Add `iv_minus_hv` and `iv_to_hv_ratio` columns to identify potentially rich option premiums relative to recent realized movement. Treat this as a ranking and investigation signal, not proof of mispricing, because high implied volatility may reflect known event risk or changing market expectations.

- Use implied volatility as the primary probability input.
   The notebook already fetches option `implied_volatility`; preserve it and use it for option probability calculations. Historical volatility can remain as a comparison or fallback.

- Add bid/ask spread diagnostics.
   Preserve bid, ask, midpoint, spread, spread percentage, quote timestamp, and quote age in the output so liquidity can be inspected before adding hard filters.

- Add option volume diagnostics.
   Preserve current daily option volume, daily trade count, daily VWAP, previous daily volume, previous daily trade count, and previous daily VWAP in the output.

- Add annualized return on collateral.
   Current `potential_return` is useful, but different expirations need an annualized comparison.

- Add moneyness metrics.
   Track percent out-of-the-money and distance-to-strike so candidates can be compared more directly.

## Future Improvements

1. Add downside stress tests.
   Show estimated loss if the underlying falls 5%, 10%, 20%, or more. A high probability of expiring worthless does not guarantee favorable tail risk.

2. Separate probability of profit from expected value.
   The Black-Scholes-style probability is a risk-neutral estimate, not a real-world win rate. Add expected value or payoff-based analysis where possible.

3. Parameterize screener settings.
   Make expiration date, risk-free rate, max collateral, minimum open interest, minimum bid, probability threshold, and liquidity thresholds configurable.

4. Backtest the screening rules.
    Test the screen across historical expirations and market regimes, including transaction costs, slippage, assignment behavior, and drawdowns.

## Immediate Cleanup

- Rotate the hard-coded Alpaca credentials in the notebook and move credentials to environment variables.
- Replace the hard-coded `2025-08-15` expiration date with a configurable future expiration.
- Add a reproducible environment file such as `requirements.txt` or `pyproject.toml`.
- Decide whether the next version should remain notebook-first or become a small Python CLI/app.
