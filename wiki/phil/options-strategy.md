# Phil's Options Strategy

## Why Options Over Stock — The Capital Problem

Phil's swing trading strategy requires entering 4–5 concurrent positions. With regular stocks, this creates a capital problem.

Example: $100,000 swing trading account. A stock at $100 with a stop at $90 (10% away) requires a **$50,000 position** to risk your planned $5,000. Two trades and your entire swing trading capital is consumed. The third setup appears on your watchlist and you cannot enter it.

Options solve this elegantly. Instead of buying $50,000 worth of stock, you buy a call option for a fraction of that cost — the **premium** — and control the same 100 shares.

**The hierarchy Phil uses:**
1. LEAPs (Long-term Equity Anticipation Securities) — preferred, highest leverage
2. Cash-Secured Puts / Covered Calls — income-oriented alternative
3. Regular stock — baseline, for accounts too small for options

Phil personally only uses LEAPs. He is explicit about this.

---

## Three Structural Advantages of Options

**1. Less capital required.** A stock at $200/share costs $20,000 to buy 100 shares. A call option on the same stock might cost $4,000 in premium for the same 100-share exposure. That frees $16,000 for other trades.

**2. Defined risk.** The premium you pay is your total maximum loss. Nothing more. If the stock drops 90% overnight, you lose only your premium — no stops can be gapped through, no slippage. "Your maximum loss is always and only the premium you paid."

**3. Over-proportional gains (leverage).** When a stock moves 20%, the option can double. When a stock moves 40%, the option can triple or more. The leverage accelerates as the position moves deeper in the money — the deeper into profit you go, the more aggressively the option tracks the underlying.

---

## The LEAPs Strategy

### What Is a LEAP?

A LEAP is a call option with an expiration date at least 12 months away. Phil uses expirations **1.5 to 2 years out**. The name stands for Long-term Equity Anticipation Security, but what matters is the practical benefit: time.

### The Only Two Decisions

When entering a LEAP, Phil makes exactly two choices:

**Decision 1 — Expiration Date: Today + 1.5 to 2 Years**

Options lose value as they approach expiration — this is called time decay (theta). The decay is not linear; it accelerates dramatically in the final weeks. The curve is flat at the start and then drops steeply as expiration approaches.

By going 1.5–2 years out, you only hold the option during the **flat part of the curve** where time decay is negligible. A trade might resolve in 2 weeks or 3 months — you will exit long before the steep decay begins. The 2-year expiry is insurance against being timed out, not a commitment to hold for 2 years.

**Decision 2 — Strike Price: At the Money (ATM)**

After your BBOS confirmation triggers, look at the current stock price and choose the strike price **closest to that price**. That is ATM — at the money.

No complex analysis of which strike to pick. Just ATM. The ATM strike provides a balanced combination of leverage and cost that works well for this strategy.

### No Stop Loss Needed

With regular stock trades, you calculate a stop loss level and risk a defined dollar amount if that level is hit. With LEAPs, the stop loss mechanism is built in:

- Maximum loss = the premium you paid
- If your max risk per trade is $5,000 and one LEAP contract costs $4,600, that is your risk. Period.
- You cannot lose more than your premium regardless of what the stock does

Position sizing becomes simple: if your max risk per trade is $5,000, buy as many contracts as you can without exceeding $5,000 in total premium.

### Take Profit

**One contract:** Close at **+100%** (you doubled your money). With a 70–80% win rate, this produces strong returns over time.

**Multiple contracts:** Close **partials at +100%**, let the remainder run to the resistance level you identified on the monthly chart. Then close the remaining contracts at resistance.

Phil's Apple example from the tutorials: Apple trading at $255. Choose January 2028 $260 calls (today + ~2 years, ATM). Premium: $46/share × 100 = **$4,600 per contract**. This fits within the 5% rule on a $100K account. Exit at +100% premium or at the next monthly resistance.

---

## ITM, ATM, OTM — What They Mean

For a call option on a stock trading at $185:

| Category | Strike | Premium | Notes |
|---|---|---|---|
| In the Money (ITM) | Below $185 (e.g., $170) | Most expensive | Has intrinsic value already |
| At the Money (ATM) | ~$185 | Medium | Phil's chosen strike |
| Out of the Money (OTM) | Above $185 (e.g., $200) | Cheapest | Needs a bigger move to be profitable |

Phil chooses ATM because it provides the right balance. OTM options are cheaper but require a larger move to profit, and their leverage comes with higher risk of expiring worthless.

---

## Cash-Secured Puts and Covered Calls

Phil teaches this as an alternative for traders who prefer income/cash flow over leveraged returns. He does not personally use it — but explains it for completeness.

The philosophy shifts: instead of buying options, you **sell** them and collect the premium.

### Phase 1: Entry — Sell a Cash-Secured Put

After your confirmation signal:
- Sell a put option with strike = your intended entry price, expiration = ~2 months out
- You receive the premium immediately (cash in your account)
- If the stock drops to your strike by expiration → you get assigned 100 shares (which you wanted) plus you keep the premium
- If the stock stays above your strike → the put expires worthless, you keep the premium, and try again

"Cash-secured" means you have sufficient cash to buy the 100 shares if assigned.

### Phase 2: Hold Regular Stock

While in the position, you hold the regular stock. Nothing fancy — you ride the wave exactly like a normal stock trade.

### Phase 3: Exit — Sell a Covered Call

When price approaches your take profit:
- Sell a call option with strike = your intended exit price, expiration = ~2 months out
- Receive the premium again
- If the stock rises above your strike → your 100 shares get sold at your target price (which you wanted) plus you keep the premium
- If the stock stays below → the call expires worthless, you keep the shares and the premium, try again

Total extra return from using this strategy: approximately **10–15% on top of the regular trade return** — collected via premiums on both entry and exit. Warren Buffett used this exact approach at scale with multi-year expirations.

---

## LEAPs vs Cash-Secured Puts/Covered Calls — When to Use Which

| | LEAPs | CSP / Covered Calls |
|---|---|---|
| What you hold | Options | Regular stock |
| Capital needed | Less (just premium) | More (100+ shares) |
| Leverage | High — over-proportional gains | Low — regular stock returns + premium |
| If right | Can 2x, 3x, 5x+ | Regular gain + 10–15% premium |
| If wrong | Lose all the premium | Lose on stock, offset by premium received |
| Stop loss needed | No (premium = built-in risk cap) | Yes — regular stop loss applies |
| Phil's preference | Yes — this is what he uses | No — but he teaches it |

**Choose LEAPs if:** you want maximum leverage, have moderate capital ($25K+), and are comfortable with the premium going to zero if wrong.

**Choose CSP/CC if:** you want income/cash flow, have larger capital (enough for 100+ shares), and prefer reducing risk via premium offset.

---

## Greeks Phil Focuses On

Phil does not discuss all Greeks extensively, but the relevant ones in his framework:

**Theta (time decay):** The reason for going 1.5–2 years out on expiration. Phil explicitly references the time decay curve — flat early, steep near expiry. By exiting long before expiry, you operate only on the flat part.

**Delta:** Implicitly relevant through the ATM strike choice. ATM options have a delta of approximately 0.5, meaning the option moves about $0.50 for every $1 the stock moves. As the option goes ITM, delta increases toward 1.0 — this is the leverage acceleration Phil describes.

Phil does not teach options Greeks as a standalone subject. The practical rules (ATM strike, 2-year expiry, premium = risk) are designed to make Greek management automatic rather than requiring manual calculation.

---

## Small Account Considerations

If your account is too small to afford LEAP premiums within your 5% risk rule:

- Trade **cheaper stocks** (lower stock price = cheaper options)
- Trade **less volatile stocks** (lower volatility = cheaper premiums)
- Use **3x leveraged stocks** (e.g., TQQQ) instead of options — they achieve similar leverage without option mechanics
- Or simply buy regular stock until the account grows enough to afford LEAPs

Do not use LEAPs on positions that would require risking more than 5% of your account to buy even one contract.

*Last updated: 2026-05-19 — built from 14 tutorial transcripts*
