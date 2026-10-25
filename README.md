# GROW — Agricultural Intelligence and Crop Recommendation System

GROW is a data-driven agricultural intelligence platform focused on Kerala, India. It assists farmers and agricultural planners in identifying suitable crops based on soil characteristics, weather trends, historical yield, market prices, cultivation costs, and crop calendars.

## Current Project Status: Phase 1 Complete

- **Environment**: Python 3.14.7, Node.js v24.21.0, npm 11.19.0.
- **Data Engine**: Native Python `csv`, `json`, and `sqlite3` paired with `numpy`, `scipy`, and `scikit-learn` (Windows Application Control blocks `pandas` Cython extensions).
- **Core Datasets Audited**:
  - `crops.csv`: 10 Kerala crops and agronomic constraints.
  - `soil.csv`: 23 soil records across 13 Kerala districts with qualitative pH and texture classes.
  - `soil_crop_suitability_v2.csv`: Rule-based 3-factor heuristic score.
  - Ingestion pipeline queued for Weather (NASA POWER), Yield, Market Prices, and Cultivation Costs.

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
```
