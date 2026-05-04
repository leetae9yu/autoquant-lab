# CRSP requirements for DDQM2, S&P 500 adaptation

This file lists the minimum data needed to adapt DDQM2 to the S&P 500 universe.

## 1) Core CRSP fields

Use `crsp.dsf` for daily work or `crsp.msf` for monthly work.

| Need | `crsp.dsf` fields | `crsp.msf` fields | Notes |
| --- | --- | --- | --- |
| Security identifier | `permno` | `permno` | Primary key for one traded security |
| Company identifier | `permco` | `permco` | Use for company level deduping, not as the trading key |
| Date | `date` | `date` | Panel time index |
| Price | `prc` | `prc` | Use absolute value when needed, CRSP prices can be signed |
| Return label | `ret` | `ret` | Monthly label can come directly from next month `ret` |
| Volume | `vol` | `vol` | Trading volume |
| Shares outstanding | `shrout` | `shrout` | Usually in thousands, confirm unit handling in the pipeline |
| Split adjustment | `cfacpr` | `cfacpr` | Needed if you rebuild adjusted prices |
| Share adjustment | `cfacshr` | `cfacshr` | Needed if you rebuild adjusted shares |
| Non delisting return, optional | `dlret` | `dlret` if available | Useful if you want total return labels that capture delistings |

## 2) Minimum fields for 1 month forward returns

For monthly labels, the minimum set is:

- `permno`
- `date`
- `ret`

Label construction:

- Sort by `permno`, then `date`
- Shift `ret` forward one month within each `permno`
- If you use daily data instead, compound future daily `ret` values over the next 1 month window

Recommended extras for cleaner labels:

- `dlret`, then combine with `ret` when a stock delists
- `permco`, for company level consolidation when multiple share classes exist

## 3) Minimum fields for features

For DDQM2 features, keep these fields:

- Price, `prc`
- Volume, `vol`
- Shares outstanding, `shrout`

If you need split adjusted inputs, also keep:

- `cfacpr`
- `cfacshr`

## 4) S&P 500 universe filter

Do **not** filter by `ticker`.

Use one of these routes instead:

### Option A, CCM link history route

Start from a Compustat S&P 500 membership source, then map into CRSP with `ccmxpf_lnkhist`.

Relevant CCM fields:

- `gvkey`
- `lpermno`
- `lpermco`
- `linkdt`
- `linkenddt`
- `linktype`
- `linkprim`

Suggested rule:

- Keep valid links where `linktype` is typically `LC`, `LU`, or another approved CRSP Compustat link type used by the project
- Keep primary links, usually `linkprim` in `P` or `C`, depending on the mapping rule you standardize on
- Apply the date range with `linkdt` and `linkenddt`

### Option B, CRSP index route

If you have a CRSP S&P 500 constituent or index membership table, use that directly.

That route should already give you the security identifier, so the important join key is still `permno`, not `ticker`.

## 5) Why PERMNO and PERMCO matter

- `permno` is the stable security identifier in CRSP
- `permco` groups multiple share classes under one company
- `ticker` can be reused, change over time, or map to multiple securities

For this reason, the pipeline should be built on `permno`, with `permco` used only when you intentionally collapse to the company level.

## 6) Fallback plan if WRDS CRSP is unavailable

Use `yfinance` only as a backup.

Fallback fields:

- `Close` or `Adj Close` for price and return labels
- `Volume` for volume
- `sharesOutstanding` from ticker metadata when available

Fallback process:

1. Pull an S&P 500 ticker list from a public source
2. Download prices with `yfinance`
3. Build 1 month forward returns from adjusted prices
4. Treat ticker membership as temporary, and record that the output is not CRSP grade
5. Re map to `permno` and `permco` once WRDS access returns

Fallback warning:

- This path is vulnerable to ticker reuse, stale membership, corporate action noise, and missing shares outstanding values
- Use it for prototyping only, not as a final replacement for CRSP
