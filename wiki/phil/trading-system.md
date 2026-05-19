# Phil's Swing Trading System — End to End

## The Foundation

Phil's swing trading system is built on one insight: probabilities compound when you are patient. Think of it like poker — a real poker strategy means folding 80% of hands. You wait, skip setup after setup, and then when two aces appear you play with full conviction because the odds are stacked in your favour. The system is designed so that 99.9% of your time is waiting, and 0.1% is execution. That is not a flaw — it is the design.

The system works on all asset classes and all timeframes, but the **monthly + daily combination produces the highest win rate and the best risk-to-reward ratios with the least effort**. For the stock universe, Phil restricts his universe to stocks with a **market cap over $200 billion** (minimum $100B). These companies have an inherent upward bias, rarely go insolvent, have deep options liquidity, and their price action on the monthly chart is clean and readable.

---

## The Three-Step Process: Trend → Structure → Confirmation

### Step 1 — Identify the Trend (Monthly Timeframe)

Open a naked chart on TradingView. Switch to the **monthly timeframe, logarithmic view**. Zoom out to see at least 10–20 years of history.

Ask one question: **Does the chart move from bottom-left to top-right?**

- **Uptrend** (higher highs and higher lows) → look for setups
- **Sideways** → can still trade, not ideal
- **Downtrend** (lower highs and lower lows) → **do not trade**

This takes about two seconds per chart. Do not overcomplicate it. One messy candle does not change the trend — look at the overall picture.

### Step 2 — Identify Structure (Monthly Timeframe)

Still on the monthly chart, identify clear **support levels**. There are three types:

- **Horizontal Support (HS)** — two or more touch points at roughly the same horizontal price zone
- **Trend Line Support (TS)** — ascending diagonal connecting two or more higher lows
- **Confluence of Support (COS)** — two independent support levels converging at the same area (e.g., HS + TS)

The Confluence of Support is the highest probability setup. Once identified, **place an alert at the level**. If the market is not at support, there is no trade. Do nothing until the alert triggers.

Only draw obvious levels. If you have to force it or squint to see it, skip it. The more obvious the setup, the higher the probability it plays out.

### Step 3 — Confirmation (Daily Timeframe)

When an alert triggers, drop to the **daily chart**. You will see the pullback to monthly support as a daily downtrend — lower highs and lower lows. This is normal and does not invalidate the monthly uptrend.

Look for one signal: a **Bullish Break of Structure (BBOS)**. Specifically:

1. Identify the most recent **previous lower high** on the daily chart (use the wick, the actual highest point reached)
2. Wait for price to break **above** that level with **two consecutive daily candle closes** above it
3. That break = your confirmation signal

Two entry methods:
- **Breakout entry** — enter as soon as the second candle closes above the level (earlier, potentially better price)
- **Break and Retest entry** (preferred) — wait for price to pull back to the broken level, which now acts as support, and enter on the bounce

If the retest never comes, do not enter. There is no harm in skipping a trade.

---

## Stop Loss Placement

After confirming on the daily, **go back to the monthly chart** to place the stop.

Stop loss goes **below the monthly support level, with room to breathe.** Not immediately below it — typical distance is 10–25% depending on the asset's volatility. Large-cap stocks may still need 20% stops because daily candles can briefly pierce monthly support without invalidating it. Monthly support is only invalidated by monthly candles closing below the level — what happens on the daily stays on the daily.

**Never move your stop loss against yourself.** If you set it, honour it.

---

## Take Profit Placement

Two scenarios:

**Scenario 1 — Resistance exists above price:** Place take profit at the next clear monthly resistance. Take partial profits (40–50% of the position) when price reaches resistance. Let the remainder run.

**Scenario 2 — No resistance above (e.g., all-time high break):** Use a **bearish Break of Structure on the daily** as your exit signal. As long as the daily shows higher highs and higher lows, stay in the trade. When the daily shifts to a downtrend (break below previous higher low), take partials and eventually close the position.

Always take partial profits rather than closing everything at once. This lets you lock in gains while keeping exposure if the trend continues.

---

## Risk-to-Reward Check

Before entering, calculate the RRR using TradingView's measurement tool:

**RRR = Distance to Take Profit ÷ Distance to Stop Loss**

- Below 1:1 → **do not take the trade**
- 1:1 → acceptable
- 1:2 → good
- 1:3 or better → excellent

With a 60–80% win rate and minimum 1:1 RRR, the strategy is consistently profitable.

---

## Position Sizing

**Maximum 5% of total swing trading capital per trade.** Maximum ~5 concurrent trades, for a total open risk of ~20%.

For regular stocks:
- **Position Size = Risk Amount ÷ % Distance to Stop Loss**
- Example: $5,000 risk on a 10% stop → $50,000 position

This capital consumption problem is why Phil uses **LEAP options** — they require far less capital per position while maintaining the same dollar risk, freeing up capital for multiple concurrent trades.

---

## Managing Trades Once In

Once you enter:
1. Place an alert at your stop loss level
2. Place an alert at your take profit level
3. **Do nothing until the next alert triggers**

Do not watch the daily chart between alerts. What happens day-to-day is irrelevant — the analysis was done on the monthly, the stop and target are set. Looking at the account between alerts only damages your psychology.

---

## Adding to Winners

Phil does not typically add to positions after entry in the same way some traders pyramid. The framework for multiple contracts is: hold multiple LEAP contracts, take partial profits at 1:1 (close 40–50% of contracts), let the remaining contracts run to resistance or the all-time high target.

---

## What Invalidates a Setup

- Monthly candle **closes** below the support level (not a wick — closes)
- Risk-to-reward falls below 1:1 before entry
- Market is not at support (there is simply no trade)
- No confirmation signal appears on the daily after the alert triggers
- Breakout entry attempted on a single candle with no follow-through (false breakout — wait for two candle closes)

---

## Rules That Are Absolute

- Only trade uptrends on the monthly chart
- Only buy at support — never in the middle between support and resistance
- Stop loss is always placed; never widened after the fact
- RRR must be 1:1 minimum before entry
- Maximum 5% risk per trade, ~5 concurrent positions
- Monthly support is only invalidated by monthly candles — daily noise is irrelevant

*Last updated: 2026-05-19 — built from 14 tutorial transcripts*
