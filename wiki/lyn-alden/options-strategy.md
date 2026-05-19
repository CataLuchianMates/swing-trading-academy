---
title: "Options Strategy"
wiki: "lyn-alden"
last_updated: "2026-05-18"
---

# Lyn Alden: Options Strategy

## Philosophy: Options as Entry and Income Tools

Lyn uses options in a fundamentally different way than most traders. She is not speculating on directional moves in the short term. Instead, she uses options as tools to:

1. **Enter positions at a discount** via cash-secured puts — getting paid to wait for the stock to come to her
2. **Generate income** on existing positions via covered calls
3. **Take directional long-term exposure** via LEAP calls on high-conviction theses with defined maximum loss

She never uses leverage in her options strategies. Every put is cash-secured (she has the cash to buy the stock at the strike). Every call she sells is covered (she owns the underlying). Every LEAP she buys is a small position sized for total loss.

Her rule: "My view has been to avoid using leverage or naked options." Position sizing is always sized such that full assignment or full loss of the option premium would not materially impair the portfolio.

## Cash-Secured Puts: Entry at a Discount

The cash-secured put strategy is Lyn's primary options tool for initiating new stock positions.

**Mechanics**: Sell a put option at a strike price below the current market price. Collect the premium upfront. If the stock falls below the strike by expiration, you are "put" the stock (obligated to buy at the strike). Your effective cost basis is the strike minus the premium collected. If the stock stays above the strike, the put expires worthless and you keep the premium as income.

**Why this works for her approach**: Lyn is a value investor who wants to buy stocks at attractive prices. The put strategy lets her set a price limit she'd be happy to own the stock at, and earn a yield while waiting. If she never gets assigned, she earned the premium. If she does get assigned, she got the stock at her desired price minus a premium discount.

**Key examples across the articles**:

---

**AMD Cash-Secured Puts (April 2025)**:
- AMD trading ~$90 at time of mention
- Strike: $80 June 2025 puts
- Premium: $4.60 (~5.7% of the strike in approximately 2 months)
- Rationale: AMD had sold off during tariff panic. Lyn was comfortable owning AMD at $80 or below. $4.60 premium in 2 months was an attractive income rate if not assigned. If assigned, effective cost basis = $80 - $4.60 = $75.40.
- She described AMD as being in the "10% growth pie" of her newsletter portfolio after initiating this.

---

**MSTR Cash-Secured Puts (September 2025)**:
- MSTR trading around $250-260
- Strike: $250 or $260 January 2026 puts
- Rationale: Lyn noted this as an idea rather than a firm action — she was considering whether put-selling on MSTR could generate income while maintaining potential bitcoin treasury company exposure. High implied volatility in MSTR options means premium income is substantial.

---

**Micron (MU) Cash-Secured Puts (April 13, 2026)**:
- MU trading at $420
- Strike: $380 June 18, 2026 puts
- Reasoning: "I'll be selling Micron June 18 cash-secured puts at a strike price of $380. This'll pay a decent premium during the two months until expiry, and if the stock price drops it means I'll be entering at a cost basis in the ballpark of $350."
- Position sizing caveat: "I do recommend conservative position sizing with a stock that moves this sharply."

The MU puts worked out in Lyn's favor — the stock broke out to new highs by May 2026, and the puts expired worthless (keeping the premium).

---

## Covered Calls: Income and Disciplined Exits

Covered calls are Lyn's secondary options tool. She uses them in two contexts:

1. **Income generation on positions she'd be happy to hold or sell** at the strike price
2. **Trimming overextended positions** where the premium effectively helps crystallize a partial exit

**GDX Covered Calls (October 2025)**:
- Sold GDX (Gold Miners ETF) covered calls at $85 January 2026 strike
- Context: Gold had become "most overbought monthly RSI in history" — Lyn was cautious about adding new exposure and used covered calls to effectively commit to a partial exit if gold continued to rally
- Outcome: Gold soared further in November/December 2025. The $85 calls were exercised in December/January as GDX exceeded that strike. Lyn's February 2026 portfolio update noted: "GDX is no longer in the portfolio. It was automatically exited with a major gain due to covered calls being exercised amid soaring prices."
- This is a textbook "disciplined exit through covered calls" outcome — she got paid premium AND was forced to take profits on an overextended position.

---

## LEAP Calls: Long-Term Directional Exposure

Lyn's LEAP strategy (Long-term Equity Anticipation Securities — options with expirations typically 12-24 months out) is primarily used for concentrated directional bets with defined maximum loss.

**Core principles she applies to LEAPs**:
- ATM (at-the-money) or near-ATM strikes to maximize delta and minimize time value waste
- Minimum 12-month expiration, ideally 18-24 months, to give the thesis time to play out without being harmed by near-term volatility
- Small position sizing as a percentage of portfolio (the LEAP is like a highly leveraged position, so small notional = large exposure)
- Used when she has high conviction on a long-term move but wants to define maximum loss

She does not frequently describe LEAP positions explicitly in the newsletter articles, but does reference the instrument type (e.g., Phil's strategy which Lyn would be familiar with uses LEAPs with minimum 13-14 months expiry on monthly-support confirmed entries).

---

## Position Sizing Framework

Lyn's position sizing for options follows from her broader portfolio philosophy:

**Put-selling positions**: Sized so that full assignment results in a position weight she'd be comfortable with long-term. If she wouldn't be comfortable owning a 5% position in the stock, she shouldn't sell puts that could result in a 5% position.

**Covered call positions**: Sized to match existing stock position. If she'd be comfortable selling 100% of a stock at the strike, sell the full covered call. If she only wants to trim half, sell puts on half.

**LEAP positions**: Sized as a small percentage of total portfolio (1-3% of portfolio = ~10-15% of position size vs outright stock). The LEAP could go to zero, so the notional size must be survivable.

**Volatility awareness**: She explicitly noted for MU puts that conservative position sizing is needed because "a stock that moves this sharply" requires smaller sizing than less volatile positions. High-volatility stocks generate high premium income, but the assignment risk is real — the premium reflects actual probability of being assigned, not "free money."

---

## Options and Tax Considerations

Lyn references options within tax-sensitive portfolio management contexts:

- Late 2025 saw many investors selling bitcoin for "capital gains losses to offset gains elsewhere" — tax-motivated selling contributed to the November-December 2025 correction
- Her covered call on GDX was part of a portfolio management approach that accepted potential assignment at a profit rather than holding for a possible future downturn
- Cash-secured puts, when the put expires worthless, generate short-term ordinary income (the premium) — tax-inefficient compared to long-term capital gains, but she views the income generation as worth the cost for high-premium situations

---

## Summary of Options Trades in the Article Corpus

| Date | Ticker | Type | Strike | Expiry | Premium/Context |
|------|--------|------|--------|--------|-----------------|
| Apr 2025 | AMD | Cash-secured put | $80 | June 2025 | $4.60 (~5.7% in 2 months) |
| Sep 2025 | MSTR | Cash-secured put idea | $250/$260 | Jan 2026 | High-vol premium noted |
| Oct 2025 | GDX | Covered call | $85 | Jan 2026 | Exercised for major gain |
| Apr 2026 | MU | Cash-secured put | $380 | June 2026 | Expired worthless (profitable) |
