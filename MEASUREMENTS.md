# Local measurements — 2026-11-13

Scored on the kit's six practice cases with the pinball loss the rules define
(`100 x max(tau*(y-q), (tau-1)*(y-q))`, averaged over every case, market, minute
and quantile), so a lower number is better.

## The harness was checked against the house's own published numbers

The kit answers p00..p04 locally (their 240 scored minutes are the tails of
p01..p05). p05's own four hours are not in the kit, so they were fetched from
Polymarket's public `prices-history` and put on the house's grid (a minute takes
the last point at or before its first second). Before trusting that, the same
code rebuilt a window the kit already holds: **24 of 24 markets reproduced the
kit's prices exactly**.

With that, the house baseline (starter/main.ts) scores:

| | this harness | the rules' published value |
|---|---|---|
| loss | **0.363589** | 0.363589 |
| median error | **0.767503** | 0.767503 |
| 90% coverage | **0.9496** | 0.949642 |

All three agree, so the measurement below is the same measurement the board makes.

## The final model, per case

`main.py`: each market's own history gives the h-step move distribution in
logit space; the median stays at the last price; the spread is scaled by the
square root of the market's recent-to-full volatility ratio times the case's
median ratio, and by a width factor of 0.80.

| case | house | this entry | coverage_90 |
|---|---|---|---|
| p00 | 0.536138 | 0.507381 | 0.7570 |
| p01 | 0.380352 | 0.314545 | 0.8996 |
| p02 | 0.408408 | 0.380367 | 0.7002 |
| p03 | 0.368599 | 0.267104 | 0.8835 |
| p04 | 0.298794 | 0.195986 | 0.8493 |
| p05 | 0.238232 | 0.113234 | 0.9191 |
| **pooled (128 markets)** | **0.363589** | **0.284439** | 0.8402 |

That is 0.079150 below the house baseline, or 21.8% lower.

## What was tried and rejected, with numbers

| model | pooled loss |
|---|---|
| house baseline (sigma 0.0025, median at x) | 0.363589 |
| per-market empirical deltas, median kept | 0.385286 |
| same, median pinned to x | 0.310738 |
| same, width 0.90 | 0.301951 |
| pooled cross-market shape, per-market sigma | 0.304564 |
| volatility-conditioned (rescaled) deltas | 0.331240 |
| house-style width floor under the empirical band | 0.295272 |
| final: own empirical shape + case volatility, width 0.80 | **0.284439** |

The conditioning and the floor both looked right on paper and both lost: the
band that pays is the market's own jump history, narrowed, with the case-wide
volatility as the only cross-market signal that helped.

## Runtime and determinism

Each case runs in 184-256 ms (limit 8 s), and two runs of every case are
byte-identical.
