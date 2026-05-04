# IBES requirements for DDQM2 S&P 500 adaptation

This note maps the IBES analyst estimate inputs needed to adapt DDQM2 to the S&P 500 universe.

## 1. Required IBES inputs

Use IBES Summary History as the primary source when possible, and Detail History when a feature needs per analyst observations.

### Core summary fields

* `ibes.statemu`, the main summary estimate, usually the consensus mean for the target fiscal period.
* Estimate date or period stamp, so every value can be tied to the date it became visible.
* Fiscal period identifiers, such as fiscal year and quarter.
* Standard deviation or dispersion, needed for analyst disagreement features.
* Number of estimates, used as a coverage proxy.
* High, low, median, and mean estimates if available.
* Revision counts, split into upward and downward changes.

### Detail level fields when summary data is not enough

* Individual analyst estimate values.
* Analyst identifier or broker code.
* Estimate timestamp or announcement date.
* Revision direction, up or down, relative to the prior estimate.
* Filter flags for stale, inactive, or duplicate estimates.

### Feature set to build

* EPS consensus level.
* Dispersion, measured by standard deviation.
* Revision intensity, upward and downward.
* Coverage breadth, measured by number of estimates.
* Optional surprise style features, if actuals are available later for validation only.

## 2. Security linkage to CRSP

IBES security identifiers are not a direct substitute for CRSP identifiers.

### Identifier chain

* `TICKER` identifies the IBES security name used in analyst records.
* `CUSIP` helps bridge IBES and market data, but it can change over time.
* `IKEY` is the internal IBES security key and is often the safest IBES side identifier.
* CRSP uses `PERMNO` as the stable security identifier.

### Recommended link path

Use the WRDS linking table `wrdsapps.ibcrsphist` to map IBES `TICKER`, `CUSIP`, or `IKEY` onto CRSP `PERMNO`.

Practical rule:

* Start with the most specific valid IBES security key available.
* Apply the historical date range in the link table.
* Keep only links valid on the estimate date, not just the current link.
* If multiple matches exist, prefer the one with the best overlap on CUSIP and date validity.

## 3. Lookahead bias controls

Analyst estimates are time sensitive. A bad join can leak information from the future.

### Main risks

* Using estimates after the portfolio formation date.
* Joining by fiscal period only, without the estimate announcement date.
* Using revised consensus values that were not public yet on the signal date.
* Carrying forward the latest consensus from after earnings were announced.

### Safe timing rule

For each rebalance date, use only estimates with an announcement or update date strictly earlier than the rebalance cut off. If the data vendor supplies snapshot dates, use the latest snapshot that would have been known at that time.

### Validation checks

* Confirm every feature is lagged by at least one trading day, or by the vendor publication delay.
* Rebuild a small sample manually and verify the visible consensus matches the historical timestamp.
* Drop observations where the link date and estimate date do not overlap cleanly.

## 4. Fallback plan if WRDS IBES is unavailable

If IBES access is missing or incomplete, keep the model path alive with simpler inputs.

### Option A, public consensus proxy

* Use public earnings consensus feeds if they provide estimate level, dispersion, and revision direction.
* Preserve the same feature names where possible so the downstream pipeline stays stable.

### Option B, reduce the feature set

* Remove analyst based features entirely.
* Replace them with price, volume, volatility, and fundamentals already available in CRSP or Compustat.
* Keep the S&P 500 universe and the same rebalance schedule so the experiment remains comparable.

### Option C, hybrid mode

* Use analyst features only for names with valid IBES history.
* Fill missing names with neutral values and a missingness flag.
* Report the coverage ratio so results are easy to interpret.

## 5. Minimal implementation checklist

* Build the IBES to CRSP link through `wrdsapps.ibcrsphist`.
* Require historical validity on every link.
* Lag all estimate features to prevent lookahead bias.
* Add dispersion and revision features from Summary History or Detail History.
* Provide a public data or no analyst feature fallback.
