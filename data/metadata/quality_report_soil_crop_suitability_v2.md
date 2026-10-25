# Data Quality Report: Soil-Crop Compatibility Matrix (Heuristic v2)

- **Dataset Identifier:** `soil_crop_suitability_v2`
- **Target File:** `data/soil_crop_suitability_v2.csv`
- **Generated At:** 2026-10-25 12:46:57
- **Overall Status:** PASS (Valid)

## Summary Metrics

| Metric | Value |
| :--- | :--- |
| Total Records | 230 |
| Total Columns | 9 |
| Total Missing Values | 50 |
| Duplicate Records | 0 |
| Schema Compliance | 100% |

## Missing Values by Column

| Column | Missing Count | % Missing |
| :--- | :--- | :--- |
| `district` | 0 | 0.0% |
| `soil_type` | 0 | 0.0% |
| `crop` | 0 | 0.0% |
| `texture_score` | 0 | 0.0% |
| `drainage_score` | 0 | 0.0% |
| `estimated_ph_score` | 50 | 21.7% |
| `suitability_score` | 0 | 0.0% |
| `ph_status` | 0 | 0.0% |
| `score_method` | 0 | 0.0% |

## Known Agricultural Data Limitations

- Scores are derived from rule-based heuristic formulas, NOT statistically trained or field-calibrated ML models.
- Estimated pH scores rely on midpoint mappings of qualitative descriptions.