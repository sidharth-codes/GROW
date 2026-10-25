# Data Quality Report: Kerala Statewide Cost A by Crop and Season

- **Dataset Identifier:** `cultivation_cost_a`
- **Target File:** `C:\Users\Sidhu\Desktop\new\GROW\data\processed\kerala_statewide_cost_a_timeseries_2014_15_to_2023_24.csv`
- **Generated At:** 2026-10-25 18:05:26
- **Overall Status:** PASS (Valid)

## Summary Metrics

| Metric | Value |
| :--- | :--- |
| Total Records | 350 |
| Total Columns | 11 |
| Total Missing Values | 0 |
| Duplicate Records | 0 |
| Schema Compliance | 100% |

## Missing Values by Column

| Column | Missing Count | % Missing |
| :--- | :--- | :--- |
| `crop` | 0 | 0.0% |
| `season` | 0 | 0.0% |
| `cost_year` | 0 | 0.0% |
| `cost_a_rs_per_hectare` | 0 | 0.0% |
| `state` | 0 | 0.0% |
| `source` | 0 | 0.0% |
| `source_page` | 0 | 0.0% |
| `source_url` | 0 | 0.0% |
| `retrieved_at` | 0 | 0.0% |
| `source_verification_status` | 0 | 0.0% |
| `notes` | 0 | 0.0% |

## Known Agricultural Data Limitations

- Statewide Cost A per hectare only; it is not district-specific, full Cost C, total farmer cost, profit, or ROI.
- All 108 zero values are preserved exactly as printed; they may indicate crops/years not covered or not reported and are not interpreted as zero cost.
- This dataset must not be used to calculate farm or district profitability.
- All 350 crop/season/year values were cross-checked against table A5.1 in the official Kerala DES 2023-24 report.

## External source verification

- **Report landing page:** https://ecostat.kerala.gov.in/publication-detail/report-on-cost-of-cultivation-of-important-crops-in-kerala-2023-24
- **Downloaded source PDF:** https://ecostat.kerala.gov.in/storage/publications/1905.pdf
- **Retrieved:** 2026-10-25T12:30:34+00:00
- **Table:** A5.1, printed pages 264-266; Cost A per hectare, statewide.
- **Comparison:** 350 of 350 crop/season/year values matched; 0 mismatches and 0 missing source values.
- **Zero values:** 108 retained exactly as printed; the report/pack does not establish that these are actual zero costs.
- **Use restriction:** statewide Cost A is not district-specific or full Cost C and is not used for profitability.
