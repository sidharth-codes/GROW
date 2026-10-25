# Data Quality Report: Historical Agricultural Market Prices

- **Dataset Identifier:** `market_prices`
- **Target File:** `data\processed\market_prices.csv`
- **Generated At:** 2026-10-25 19:20:12
- **Overall Status:** PASS (Valid)

## Summary Metrics

| Metric | Value |
| :--- | :--- |
| Total Records | 97 |
| Total Columns | 10 |
| Total Missing Values | 0 |
| Duplicate Records | 0 |
| Schema Compliance | 100% |

## Missing Values by Column

| Column | Missing Count | % Missing |
| :--- | :--- | :--- |
| `date` | 0 | 0.0% |
| `district` | 0 | 0.0% |
| `market` | 0 | 0.0% |
| `crop` | 0 | 0.0% |
| `variety` | 0 | 0.0% |
| `min_price` | 0 | 0.0% |
| `max_price` | 0 | 0.0% |
| `modal_price` | 0 | 0.0% |
| `price_unit` | 0 | 0.0% |
| `source` | 0 | 0.0% |

## Known Agricultural Data Limitations

- Wholesale APMC terminal market prices; farm-gate prices received by smallholders may be discounted by intermediary margins.
- The Data.gov.in current-price resource does not provide a unit in its record fields or metadata; those raw price values are retained unchanged and must not be interpreted as INR/quintal.