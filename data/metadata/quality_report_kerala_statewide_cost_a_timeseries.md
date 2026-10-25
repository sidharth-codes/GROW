# Reference Data Quality Report: Kerala Statewide Cost A Time Series

- **Reference file:** `data/reference/kerala_statewide_cost_a_timeseries_2014_15_to_2023_24.csv`
- **Canonical validated file:** `data/processed/kerala_statewide_cost_a_timeseries_2014_15_to_2023_24.csv`
- **Official source:** Kerala DES Cost of Cultivation Report 2023-24
- **Report URL:** https://ecostat.kerala.gov.in/publication-detail/report-on-cost-of-cultivation-of-important-crops-in-kerala-2023-24
- **Downloaded PDF:** `data/raw/cultivation_cost/kerala_des_cost_of_cultivation_2023_24_report.pdf`
- **Table:** A5.1, printed pages 264-266
- **Geographic coverage:** Kerala statewide
- **Period:** 2014-15 through 2023-24

## Verification and validation

| Check | Result |
|---|---:|
| Reference records cross-checked against the official report | 350 / 350 |
| Crop/season labels in source table | 35 |
| Years | 10 |
| Mismatches | 0 |
| Missing source values | 0 |
| Duplicate `(crop_season, cost_year)` keys | 0 |
| Zero values preserved exactly as printed | 108 |
| Canonical normalized records | 350 |
| Canonical schema validation | Passed |

The source comparison is recorded in
`data/raw/cultivation_cost/kerala_des_cost_of_cultivation_2023_24_report.metadata.json`.
The canonical schema separates crop and season while preserving the reported
value, statewide resolution, source citation, page reference, and retrieval
timestamp.

## Units and limitations

- Values are Cost A in INR per hectare, as reported in the source table.
- The data are statewide, not district or farm specific.
- Cost A is not full Cost C, total farmer cost, profit, or ROI; it is excluded
  from profitability calculations.
- The 108 source zeros remain unchanged. They may represent crops/years not
  covered or not reported and are not interpreted as measured zero cost.
- The related two-year input-cost/output-value summary is a separate dataset
  and is not verified by this table comparison.
