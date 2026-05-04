# Compustat requirements for DDQM2, S&P 500

This file maps the Compustat data needed to adapt DDQM2 to a U.S. S&P 500 universe.
It focuses on the minimum fields needed for common quant factors, point-in-time use, and CRSP linkage.

## 1. Source tables

Use these WRDS tables first:

- `comp.funda`, annual fundamentals
- `comp.fundq`, quarterly fundamentals
- `comp.ccmxpf_lnkhist`, CCM link history for Compustat to CRSP mapping

## 2. Required fields from `comp.funda`

Pull annual fields with these filters:

- `indfmt = 'INDL'`
- `datafmt = 'STD'`
- `popsrc = 'D'`
- `consol = 'C'`

| Group | Fields | Why it is needed |
| --- | --- | --- |
| Identifiers | `gvkey`, `datadate`, `fyear`, `fyr`, `curcd` | Core company key, fiscal timing, currency check |
| Balance sheet | `at`, `lt`, `seq`, `ceq`, `pstk`, `pstkrv`, `pstkl`, `act`, `lct`, `che`, `dlc`, `dltt` | Assets, liabilities, equity, leverage, liquidity |
| Income statement | `ni`, `ib`, `revt`, `cogs`, `xsga`, `xint`, `txt` | Net income, margins, profitability, tax and interest burden |
| Cash flow | `oancf`, `capx` | Operating cash flow and investment intensity |
| Capital base | `ppent`, `dp`, `xrd` | Asset quality, depreciation, R&D intensity |

### Annual fields by factor

| Factor | Minimum annual fields |
| --- | --- |
| Book Equity | `seq`, `ceq`, `pstk`, `pstkrv`, `pstkl`, `txditc` if available |
| Net Income | `ni` or `ib` |
| Operating Cash Flow | `oancf` |
| Assets | `at` |
| Liabilities | `lt` |
| Leverage | `lt`, `at`, `dlc`, `dltt` |
| Profitability | `revt`, `cogs`, `xsga`, `xint`, `ni` |

## 3. Required fields from `comp.fundq`

Pull quarterly fields with the same core filters as annual data, plus the report date:

- `indfmt = 'INDL'`
- `datafmt = 'STD'`
- `popsrc = 'D'`
- `consol = 'C'`

| Group | Fields | Why it is needed |
| --- | --- | --- |
| Identifiers | `gvkey`, `datadate`, `rdq`, `fyearq`, `fqtr`, `fyr`, `curcdq` | Quarterly key, fiscal quarter, availability date |
| Balance sheet | `atq`, `ltq`, `seqq`, `ceqq`, `pstkq`, `actq`, `lctq`, `cheq`, `dlcq`, `dlttq` | Quarter-level size, leverage, and liquidity |
| Income statement | `niq`, `revtq`, `cogsq`, `xsgaq`, `xintq`, `txtq` | Quarterly profitability and margins |
| Cash flow | `oancfy`, `capxy` | Quarterly cash flow and investment, if reported |
| Capital base | `ppentq`, `dpq`, `xrdq` | Quarter-level asset quality and growth proxies |

### Quarterly fields by factor

| Factor | Minimum quarterly fields |
| --- | --- |
| Book Equity | `seqq`, `ceqq`, `pstkq`, `pstkrq`, `rdq` |
| Net Income | `niq` |
| Operating Cash Flow | `oancfy` if present, otherwise derive from quarterly cash flow items or use annual `oancf` |
| Assets | `atq` |
| Liabilities | `ltq` |
| Profitability | `revtq`, `cogsq`, `xsgaq`, `xintq`, `niq` |

## 4. Point-in-time rules

Use the information only after it was available in the market.

1. `datadate` is the accounting period end date, not the public release date.
2. For quarterly data, use `rdq` as the availability date when it exists.
3. For annual data, use `rdq` if available in the record, or apply a conservative filing lag if it is missing.
4. Never join fundamentals to returns on the same `datadate` unless the release date is already in the past.
5. At each portfolio formation date, keep the latest record with `available_date <= asof_date`.
6. For monthly or daily backtests, shift the usable date to the next trading day after `rdq` or the conservative fallback date.
7. Keep snapshot logic or as-of extraction logic so later restatements do not overwrite the historical view.

### Safe default lag when `rdq` is missing

If a release date is missing, use a conservative lag from `datadate`:

- quarterly records, at least 45 to 60 calendar days
- annual records, at least 90 to 120 calendar days

This is a fallback, not a research-grade substitute for true filing dates.

## 5. CCM linkage, Compustat to CRSP

Use `comp.ccmxpf_lnkhist` to map `gvkey` to CRSP identifiers.

Required fields:

- `gvkey`
- `lpermno`
- `lpermco`
- `linktype`
- `linkprim`
- `linkdt`
- `linkenddt`

### Link rules

- Prefer links where `linktype` is `LC`, `LU`, or `LS`.
- Prefer primary links where `linkprim` is `P`, then `C` if needed.
- Keep only rows where the Compustat record date falls inside the link window.
- Treat open-ended `linkenddt` as active through the sample end date.
- Final security joins should use `PERMNO`, with `PERMCO` as a company-level check.
- Do not join by ticker.

## 6. Typical factor build notes

- Book Equity usually starts from shareholders’ equity, then adjusts for preferred stock and deferred taxes.
- Net Income can use annual `ni` or quarterly `niq`, depending on the signal horizon.
- Operating Cash Flow should come from `oancf` on the annual file when possible.
- Assets and liabilities are direct pulls from `at`, `lt`, `atq`, and `ltq`.
- If a factor needs trailing 12 month values, build it from the latest four quarterly records that were already public by the formation date.

## 7. Fallback plan if WRDS Compustat is unavailable

Use public sources only as a prototype path.

### Suggested fallback stack

- Yahoo Finance via `yfinance` for current financial statements and prices
- SEC EDGAR XBRL filings for filing-backed fundamentals
- Company investor relations pages for manual exports
- A local mapping table for ticker, CIK, and temporary identifiers

### What the fallback can cover

- basic income statement items
- balance sheet items
- recent quarterly and annual statements
- current market prices for sanity checks

### What the fallback cannot cover well

- reliable historical point-in-time availability
- CCM-quality `gvkey` to `PERMNO` linkage
- clean survivorship-bias control
- consistent restatement history
- full Compustat coverage for delisted names

### Fallback rule

If WRDS is down, tag the dataset as `prototype_only` and keep it separate from final research or backtests.
Do not mix public-API data with WRDS data without a clear source flag.

## 8. Minimum extraction checklist

- `comp.funda`: identifiers, assets, liabilities, equity, income, cash flow, investment
- `comp.fundq`: identifiers, report date, quarterly balance sheet, income, cash flow
- `comp.ccmxpf_lnkhist`: GVKEY to PERMNO mapping with link dates and link type
- PIT logic: `datadate` plus `rdq` or conservative lag
- Source flag: `wrds_compustat`, `wrds_ccm`, or `public_fallback`
