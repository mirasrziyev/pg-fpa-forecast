# P&G Q1 FY27 forecast (Jul to Sep 2026), blind forecast

Built only from information available before P&G's Oct 22, 2026 earnings release.
Committed on Nov 11, 2026, after the release and before I looked at the actual results. Not edited after this commit.
Independent project using public data; not affiliated with P&G; not investment advice.

| Metric | Downside | Base | Upside |
| --- | --- | --- | --- |
| Net sales ($M) | 22,262 | 22,705 | 23,148 |
| Organic growth | 0.15% | 1.15% | 2.15% |
| Fabric & Home Care sales ($M) | 7,718 | 7,874 | 8,030 |
| Baby, Feminine & Family Care sales ($M) | 5,044 | 5,147 | 5,251 |
| Beauty sales ($M) | 4,259 | 4,341 | 4,424 |
| Health Care sales ($M) | 3,205 | 3,270 | 3,334 |
| Grooming sales ($M) | 1,795 | 1,831 | 1,868 |
| Corporate sales ($M) | 242 | 242 | 242 |
| Core gross margin | 49.2% | 49.7% | 50.2% |
| Core SG&A % of sales | 25.7% | 25.4% | 25.1% |
| Core operating margin | 23.6% | 24.4% | 25.2% |
| Core EPS | $1.76 | $1.86 | $1.96 |

## Key assumptions and reasoning
- Method: each segment starts from its last-four-quarter organic growth average. A backtest on FY26 gave this method the lowest error of the three I tested (segment MAE 2.0 pts vs 2.6 for the two-year stack and for last quarter). I adjusted only where the comparison base and the latest trend agreed, by 1 pt or less.
- Fabric & Home Care +0.75%: average of the last 4 quarters (0%, 0%, 3%, 0%).
- Baby, Feminine & Family Care -0.75%: average of the last 4 quarters (0%, -4%, 3%, -2%); the most volatile segment.
- Beauty +4.5%: average 5.25%, trimmed 0.75 pt for a tough comparison (+6% last Q1) and a Q4 slowdown to 4%.
- Health Care +1.25%: average of the last 4 quarters (1%, 3%, 2%, -1%).
- Grooming +0.5%: average 1.0%, trimmed 0.5 pt for a tough comparison (+3% last Q1) and a flat Q4.
- FX +0.3%: the broad dollar index (FRED DTWEXBGS) averaged 0.55% weaker than a year earlier, times 52% of sales outside the US. An approximation: the index's currency weights differ from P&G's.
- Gross margin -180 bp: productivity +160, pricing +10, commodities -160, mix -120, product reinvestment -70.
- Pricing held at Q4's +10 bp: price added 0% to Q4 sales, and the FY27 guidance named no new price increases.
- Commodities -160 bp, slightly worse than the ~-140 bp full-year pace implied by the guided ~$1B after-tax headwind, in line with management's comment that Q1 core EPS could fall 5% or more.
- SG&A +50 bp of sales: SG&A rose 130 bp in Q4 FY26 on marketing; I assume reinvestment continues at a smaller scale.
- Below the line and shares: FY27 guidance of $150M after-tax headwinds each from interest and other non-operating income, split evenly by quarter; 20% tax rate; $1.25B of buybacks at a $146.54 average price.
- Downside and upside: organic growth ±1 pt, commodities ±50 bp, SG&A ±30 bp, FX ±1 pt.

## Versus the anchors
- Management said Q1 core EPS could fall 5% or more; my base case is -6.6% because a 180 bp gross margin decline (commodity costs and mix, with little pricing to offset them) and higher SG&A outweigh 1.15% organic growth and buybacks.
- Consensus: $1.89 EPS and $22.8B sales; my base case is $0.03 below on EPS and $95M below on sales. The sales gap explains about a quarter of the EPS gap; the rest must come from margin or below-the-line assumptions that consensus doesn't break out.