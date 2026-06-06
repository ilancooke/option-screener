# Option Screener Roadmap

This repo now contains a Python CLI/package for generating cash-secured put candidates from Alpaca market data. The screener is useful for candidate discovery, but the strategy should be tested against historical outcomes before the output is treated as a trading system.

## Future Improvement

### Backtest The Screening Rules

Build a backtesting workflow that runs the screener logic over historical dates and expirations, then measures realized outcomes through expiration.

Questions the backtest should answer:

- What were the average and median realized P/L per contract?
- What were the win rate, assignment rate, and loss rate?
- How large were the worst losses and drawdowns?
- Did candidates ranked highly by current output metrics actually perform better?
- How sensitive were results to filters such as probability, collateral, open interest, moneyness, and IV/HV ratio?
- How did performance vary across market regimes?

Implementation considerations:

- Use only data that would have been available at each historical screening date.
- Model realistic entry prices, probably bid or midpoint with slippage assumptions.
- Include transaction costs and assignment behavior.
- Track both per-contract and portfolio-level results.
- Compare ranking methods, such as `annualized_return`, `scenario_ev_return_down_20_pct`, and current one-contract-per-underlying selection.
- Store backtest runs and outputs separately from live screener output.
