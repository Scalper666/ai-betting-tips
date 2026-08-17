# Football Betting Predictions — Fully Settled Public Log

Every prediction published by [AI Betting Tips](https://ai-betting-tips.com) —
archived before kick-off, settled automatically against real final scores, and
published in full: **losing runs included**. Most tipster datasets survive on
survivorship bias; this one is the opposite experiment.

## Files

**settled_predictions.csv** — 535 published picks (356 settled).
Columns: kickoff_utc, league, home, away, market, odds (decimal, at
publication), model_confidence_pct (blended model probability), edge_pct
(expected value vs the best available price), status (won/lost/void/pending),
profit_units (flat 1-unit staking), final_score, closing_odds (last tracked
price before kick-off), clv_pct (closing line value).

**match_results.csv** — 343 final scores collected alongside the
predictions (the settlement source).

## Method, honestly

Picks come from a time-decayed Poisson goal model blended with market-implied
probabilities; a pick is only published when the blend clears the best
available price by a set margin. Full methodology, current record and the
live closing-line-value experiment: https://ai-betting-tips.com/model

## Notes

- Flat 1-unit staking; voids return the stake and are not counted as staked.
- Odds are best-available decimal prices at publication time.
- The dataset grows as new rounds settle; source pages update twice daily.
- Licence: CC BY 4.0 — cite `ai-betting-tips.com` when you use it.
