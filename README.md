# GROW — Agricultural Intelligence and Crop Recommendation System

GROW is a data-driven agricultural intelligence platform focused on Kerala, India. It assists farmers and agricultural planners in identifying suitable crops based on soil characteristics, weather trends, historical yield, market prices, cultivation costs, and crop calendars.

## Current Project Status: Phase 1 Complete

- **Environment**: Python 3.14.7, Node.js v24.21.0, npm 11.19.0.
- **Data Engine**: Native Python `csv`, `json`, and `sqlite3` paired with `numpy`, `scipy`, and `scikit-learn` (Windows Application Control blocks `pandas` Cython extensions).
- **Core Datasets Audited**:
  - `crops.csv`: 10 Kerala crops and agronomic constraints.
  - `soil.csv`: 23 soil records across 13 Kerala districts with qualitative pH and texture classes.
  - `soil_crop_suitability_v2.csv`: Rule-based 3-factor heuristic score.
  - `weather.csv`: 60,329 validated NASA POWER daily gridded estimates from 2015-01-01 through 2026-10-20 across 14 districts; 25 provider rainfall values were quarantined.
  - `crop_yield.csv`: 6,422 historical records.
  - `kerala_cost_of_cultivation_summary_2022_23_2023_24.csv`: 70 state-level report-summary rows; 69 numeric rows verified against the original DES reports, with the unreported Beans/Summer values left blank.
  - `kerala_statewide_cost_a_timeseries_2014_15_to_2023_24.csv`: 350 statewide Cost A rows, verified against Kerala DES report table A5.1; not a profitability input.

## Project Structure

```
GROW/
├── app/
│   ├── backend/              # FastAPI application (endpoints, services, schemas)
│   └── frontend/             # React + Vite interactive dashboard
├── data/
│   ├── raw/                  # Raw downloaded datasets & API responses
│   ├── processed/            # Validated & standardized CSVs
│   ├── derived/              # Calculated metrics, heuristics, model artifacts
│   └── metadata/             # dataset_registry.json & quality reports
├── data_backup/              # Phase 1 safety backup of original datasets
├── models/                   # Saved ML estimators & clustering models
├── notebooks/                # Exploratory notebooks and validation scripts
└── requirements.txt          # Python dependencies
```

## Running Verification

```bash
# Verify Python environment and dependencies
.venv\Scripts\python.exe -c "import csv, json, sqlite3, numpy, sklearn; print('All core modules functional!')"

# Start the GROW web application (serves the API and frontend on localhost:8000)
.venv\Scripts\python.exe -m app.backend.api

# Run the focused ingestion-to-recommendation workflow tests
.venv\Scripts\python.exe -m unittest tests.test_api_workflows -v
```

Open `http://127.0.0.1:8000` to use the dashboard. The frontend is served by the
same-origin Python API and uses the files under `data/` and saved metadata under
`models/`; no frontend package installation is required. The Dataset page accepts
schema-validated CSV uploads and promotes valid files to `data/processed/`.

Crop recommendations are sourced from the stored soil-crop compatibility matrix
and are explicitly labeled as heuristic scores. Weather and yield pages report
historical observations. Prices and profitability remain unavailable until their
required authentic source datasets are ingested; the application does not fill
missing values with sample results. The supplied cultivation-cost summary is
available through `GET /api/cultivation-cost-summary`; its source figures are
verified, but it remains statewide and is not used for profitability. The separately verified statewide Cost A
series is available through `GET /api/cultivation-cost-a`; it is neither
district-specific nor a full-cost measure and is also excluded from
profitability calculations.
Authentic market-arrival CSVs can be uploaded against the separate
`market_arrivals` schema and read through `GET /api/market-arrivals`; their
reported units are preserved and are not interpreted as demand.

The enrichment pack's copied datasets matched the existing project data and were
not replaced. Its five CSV templates are stored in `data/templates/` and contain
headers only; they are not observations. Provenance and current coverage are
recorded in `data/metadata/enrichment_source_registry.json` and
`data/metadata/enrichment_data_status.md`. NASA POWER responses for
2026-01-01 through 2026-10-20 were validated and merged: 4,077 records were
added across 14 districts; 25 rainfall anomalies remain quarantined with raw
response provenance. See `data/metadata/weather_collection_attempt_2026-10-25.md`.

The supplied Cost A source transcription remains preserved under
`data/reference/`; its 350 values now match the official report. Its 108 zero
values may mean not reported rather than zero cost. The nine additional
header-only templates remain isolated in `data/templates/missing_data_pack/`.
AGMARKNET/data.gov.in price ingestion uses the `DATA_GOV_IN_API_KEY` process
environment variable without logging its value. The API labels Kerala as
`Keralam`; raw responses and provenance are retained under
`data/raw/market_prices/`. On 2026-10-25, 123 records were retrieved and
validated; 97 unique records were imported for that date. The API resource
metadata does not provide a price-unit field. Those source values are retained
unchanged and marked `UNVERIFIED_SOURCE_UNIT`; the UI does not label them
INR/quintal, and profitability calculations are blocked until the unit is
verified. The official arrival-report page remains a JavaScript-only shell
rather than a verifiable dataset/schema.
