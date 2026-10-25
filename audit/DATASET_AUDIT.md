# GROW Dataset Audit

**Audited:** 2026-10-25. Counts and ranges were calculated from current CSV files using Python `csv` and the project `DatasetValidator`. For schema-backed files, the processed CSV was preferred when it existed. Zero-byte files are recorded as files present but containing no records; this is not considered data availability.

## Dataset inventory

| Dataset | File exists | Records | Date/year range | Geographic coverage | Source recorded | Validation | Used by | Status |
|---|---|---:|---|---|---|---|---|---|
| Soil reference profiles | `data/processed/soil.csv` | 23 | Not temporal | 13 districts, 15 soil types | Department of Soil Survey & Soil Conservation listed in registry; source data are qualitative references | PASS: 8 columns, 0 missing, 0 duplicates | Soil page, recommendations, clustering | Available; **not lab measurements** |
| Soil laboratory measurements | No separate dataset | 0 | — | — | — | Not applicable | Not used | Missing: quantitative N/P/K, organic carbon, EC and farm-level moisture absent |
| Crop agronomic requirements | `data/processed/crops.csv` | 10 | Not temporal | Kerala-wide | Kerala Agricultural University listed in schema/registry | PASS: 6 columns, 0 missing, 0 duplicates | Recommendations selectors; matrix generation input | Available; limited requirement fields |
| Weather (standardized) | `data/processed/weather.csv` | 56,252 | 2015-01-01–2025-12-31 | 14 districts, exactly 4,018 rows each | NASA POWER source column; registry identifies NASA POWER | PASS: 9 columns, 0 missing, 0 duplicate keys | Weather page, yield training dataset assembly | Available; gridded/reanalysis estimates, not station observations |
| Weather raw API responses | 14 files under `data/raw/weather/*.json` | Raw JSON; not CSV rows | Filenames cover 2015-01-01–2025-12-31 | One cache per Kerala district | NASA POWER endpoint in collector and source metadata | JSON files present; live retrieval not independently repeated | Reproducibility/provenance for weather pipeline | Raw artifacts present; network provenance not independently established in audit |
| Crop yield and production | `data/processed/crop_yield.csv` | 6,422 | 2001-02–2023-24 | 14 districts, 22 crops | `DES_KERALA_ECOSTAT_28` row tag; DES Kerala registry source | PASS: 8 columns, 0 missing, 0 duplicate keys | Yield page and yield/weather ML training | Available; rows are all `Annual` |
| Soil-crop suitability v2 | `data/processed/soil_crop_suitability_v2.csv` | 230 | Not temporal | 13 districts, 15 soil types, 10 crops | GROW internal heuristic schema; source/method fields in each row | PASS: 9 columns, 50 optional missing values (estimated pH), 0 duplicates | Recommendation endpoint/dashboard | Derived heuristic; not observations or trained predictions |
| Soil-crop suitability v1 | `data/soil_crop_suitability.csv` | 230 | Not temporal | 13 districts (derived from row inspection) | Internal/derived; no source registry entry | No registered v1 schema; not separately validator-certified | No current API page identified | Superseded/unused legacy output |
| Market prices | `data/market_prices.csv` (0 bytes) | 0 | — | — | Agmarknet/DMI source defined in registry | Invalid/empty; schema validator rejects zero-byte file | Market page, profitability and planned price model | Awaiting authentic data |
| Cultivation costs | `data/cultivation_cost.csv` (0 bytes) | 0 | — | — | DES/Farm Management Studies/CACP source defined in schema | Invalid/empty; schema validator rejects zero-byte file | Profitability | Awaiting data |
| Demand/market arrivals | `data/demand.csv` (0 bytes) | 0 | — | — | Agmarknet source defined in schema | Invalid/empty; schema validator rejects zero-byte file | Counted as missing in profitability; no demand analysis | Awaiting data; schema means market arrivals, not consumer demand |
| Crop calendar | No `crop_calendar.csv` | 0 | — | — | KAU/ICAR source guidance in schema | Missing | No current page/calculation | Missing |
| Crop risk observations | No risk dataset/schema found | 0 | — | — | — | Not applicable | No integrated risk engine identified | Missing |
| DES Kerala raw yield export | `data/raw/crop_yield/des_kerala_agriculture_statistics.csv` | Raw input; not recounted here | Raw input to yield pipeline | Kerala district statistics | DES Kerala fetcher and pipeline | Raw source; processed output validated | Yield ingestion | Present |
| Baseline crop/soil inputs | `data/raw/baseline_crops.csv`, `baseline_soil.csv` | 10 / 23 | Not temporal | Crop catalog / 13 soil districts | Baseline snapshots; no independent citation in the files | Matches processed baselines by file size/content headers and sample rows | Historical initial data | Present as reference copies |
| Market-price upload template | `data/raw/market_prices/market_prices_template.csv` | 3 example rows plus notice/header | Example date 2023-01-05 | Palakkad/Kollam/Wayanad sample labels | Explicit template notice; source `AGMARKNET_SAMPLE` | **Not a dataset**; excluded from records and price model | User upload guidance only | Correctly labeled template, do not ingest as source data |

## Data quality and source interpretation

- All five non-empty schema-backed processed CSVs—crops, soil, suitability v2, weather, and crop yield—passed the current schema validator. The suitability validator allows its 50 blank `estimated_ph_score` cells because that field is optional.
- A schema-valid file is not proof of scientific validity or official source provenance. Validation checks columns, types, ranges, missing required values, and duplicate primary keys; it does not independently authenticate publisher or method.
- The soil file contains qualitative category values. It does not provide the nutrient/lab measurements requested for farm-specific advice.
- The weather dataset has complete date-key coverage by row count for the requested interval and all 14 districts. Existing tests validate row schema and selected NASA response parsing. This audit did not repeat external HTTP requests or independently authenticate downloaded JSON.
- Crop yield rows identify a DES source and contain area, production, and yield. The standardized season is always `Annual`, so seasonal inference cannot be made from this dataset.
- The suitability data are derived by multiplying 23 profiles by 10 crops (230 rows). The pH component is explicitly an estimate from qualitative categories; 50 missing component scores fall back to texture/drainage scoring per the notebook methodology.
- `data_backup/` contains prior copies, including zero-byte market/cost/demand files and a 78-byte weather CSV. The application uses `data/processed/` first and root `data/` second, not `data_backup/`.

## Data-dependent features

1. Market prices and price forecasting require authenticated historical price records, valid dates/units, multiple crops/markets, and at least the configured 500 records and 24 distinct months before the project’s intended adequacy threshold is met.
2. Profitability requires matching yield, price, and cultivation-cost records. Demand rows are optional for the current arithmetic but cannot substitute for realized consumer demand.
3. District planting calendars and crop-specific risk warnings need validated source data/rules; none should be inferred from empty files or qualitative soil labels.
4. Farm-specific soil recommendations require actual georeferenced lab tests or explicit input values, distinct from the current regional soil reference CSV.
