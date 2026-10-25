# Data Quality Report: Kerala State-Level Cultivation Cost Summary

- **Dataset Identifier:** `cultivation_cost_summary`
- **Target File:** `data/processed/kerala_cost_of_cultivation_summary_2022_23_2023_24.csv`
- **Generated At:** 2026-10-25 17:39:49
- **Overall Status:** PASS (Valid)

## Summary Metrics

| Metric | Value |
| :--- | :--- |
| Total Records | 70 |
| Total Columns | 11 |
| Total Missing Values | 2 |
| Duplicate Records | 0 |
| Schema Compliance | 100% |

## Missing Values by Column

| Column | Missing Count | % Missing |
| :--- | :--- | :--- |
| `agriculture_year` | 0 | 0.0% |
| `crop` | 0 | 0.0% |
| `season` | 0 | 0.0% |
| `reported_input_cost_rs_per_ha` | 1 | 1.4% |
| `reported_value_of_output_rs_per_ha` | 1 | 1.4% |
| `currency` | 0 | 0.0% |
| `area_unit` | 0 | 0.0% |
| `source_table_label` | 0 | 0.0% |
| `source_url` | 0 | 0.0% |
| `source_status` | 0 | 0.0% |
| `notes` | 0 | 0.0% |

## Known Agricultural Data Limitations

- State-level summary only; not district or farm-specific cost data.
- Input cost and value of output retain report-defined meanings and must not be relabeled as full cost, profit, or ROI.
- All report-defined input-cost/output-value figures were independently
  cross-checked against the original Kerala DES reports; see
  `kerala_cost_summary_verification.json`.
- The 2022-23 Beans/Summer summary has no reported cost or output value; those values remain blank.

## Provenance and interpretation

- Sources: official Kerala DES 2022-23 and 2023-24 Cost of Cultivation reports.
- Verification: 34/34 reported numeric rows for 2022-23 and 35/35 for 2023-24
  matched the report tables in order; 0 mismatches.
- Source PDFs: `data/raw/cultivation_cost/kerala_des_cost_of_cultivation_2022_23_report.pdf`
  and `data/raw/cultivation_cost/kerala_des_cost_of_cultivation_2023_24_report.pdf`.
- Table pages: 2022-23 PDF pages 7-8; 2023-24 PDF pages 9-10.
- Canonical rows: 70; two blank numeric cells remain in the unreported
  2022-23 Beans/Summer row.
- Geographic resolution: statewide; these values are not district-specific.
- Do not interpret report-defined input cost or output value as full cost, profit, or ROI.
- The two blank Beans/Summer values for 2022-23 remain missing, not zero.
