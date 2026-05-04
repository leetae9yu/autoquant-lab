# autoquant-lab

Credential-safe scaffold for DDQM2 WRDS data setup.

## Start

- Copy `.env.example` to `.env`
- Install dependencies from `requirements.txt`
- Use `PYTHONPATH=src` for local imports

## WRDS-free prototype path

WRDS remains the source of record for final DDQM2 research data. Until WRDS access is available, use the yfinance S&P 500 path only for prototype plumbing checks:

```bash
PYTHONPATH=src python scripts/build_yfinance_sp500_labels.py --start-date 2020-01-01 --end-date 2020-03-31 --max-tickers 10
PYTHONPATH=src python scripts/validate_yfinance_sp500_labels.py
```

Outputs are written under `prototypes/yfinance_sp500/` and ignored by git. This current-membership public-data fallback is marked `prototype_only=True` and must not be treated as survivorship-bias-free research data.
