# GROW Project Audit

**Audit date:** 2026-10-25  
**Scope:** Current working tree, existing project datasets and model artifacts, backend/frontend workflows, tests, documentation, and local runtime checks.  
**Method:** Read-only inspection and non-destructive validation. No application code, source datasets, or model artifacts were changed for this audit. Reports were written to this new `audit/` directory.

## A. Overall verdict

**Runnable but incomplete; currently best described as functionally working but data-limited.**

The Python standard-library server starts the UI and JSON API, the main pages are connected to local project data, and the complete existing test suite passes (39 tests). The actual data support historical weather, historical yield, qualitative soil references, crop requirements, and a derived soil-crop heuristic matrix. Market prices, cultivation costs, and demand are zero-byte files; the crop calendar is absent. Accordingly, market forecasting and profitability are correctly unavailable in the current data state.

This is **not feature-complete and not ready for deployment**. A locally reproducible defect prevents the price walk-forward routine from running; the price API ingestion route has an incompatible JSON-to-CSV handoff; duplicate and non-finite CSV values can pass ingestion validation; and the local upload/server design has no authentication or CSRF protection. A live NASA/Data.gov.in network test was not performed.

## B. Actual architecture and project inventory

- **Frontend:** Static HTML, CSS, and vanilla JavaScript in `app/frontend/`. No React/Vite package manifest or build pipeline is present.
- **Backend:** Python standard-library `http.server`/`ThreadingHTTPServer` app in `app/backend/api.py`; it serves both same-origin static files and JSON routes. It is not FastAPI or Flask, and no response-schema framework is used.
- **Persistence:** CSV files under `data/` and `data/processed/`, JSON registry/metadata under `data/metadata/`, raw source files under `data/raw/`, and serialized scikit-learn models under `models/`. No application database, migrations, user/session store, or database service was found.
- **Pipelines:** NASA POWER weather collection, DES Kerala yield ingestion, Agmarknet/Data.gov.in price ingestion, schema validation, and ML training/assessment scripts are present under `app/backend/`.
- **Models:** KMeans soil clustering and a yield artifact bundle exist; the market-price metadata records a deferred assessment and no trained price artifact exists.
- **Tests:** `tests/test_dataset_manager.py`, `tests/test_ml_modules.py`, `tests/test_weather_module.py`, `tests/test_yield_and_price_pipelines.py`, and `tests/test_api_workflows.py`.
- **Notebooks:** Seven notebook paths exist. `02_data_cleaning.ipynb` through `06_price_model.ipynb` are zero-byte files and cannot be opened as notebooks. `01_data_collection.ipynb` and `07_recommendation_model.ipynb` contain cells and outputs.
- **Configuration:** `requirements.txt` is a flat list of data/ML/notebook dependencies, not a pinned or complete lockfile. No `.env.example`, deployment manifest, frontend package manifest, or API-key configuration example was found. `.gitignore` excludes virtualenvs, caches, backups, and common build folders.
- **Git state:** The worktree was already dirty at audit start: `README.md`, `notebooks/01_data_collection.ipynb`, `notebooks/07_recommendation_model.ipynb`, and untracked frontend/API/workflow-test files. Those changes were preserved; no commit, push, deployment, or cleanup was performed.

## C. Verified working behavior

1. `python -m app.backend.api` serves the UI and same-origin routes on `127.0.0.1:8000`.
2. The dashboard is populated from actual local dataset files and reports current coverage.
3. Soil and suitability CSV uploads are validated before promotion; the test suite verifies that an invalid upload is not promoted.
4. An end-to-end HTTP test uploads soil and suitability data and obtains a score from the newly ingested matrix.
5. Recommendations are traced to the stored heuristic matrix and label their score as a heuristic, not a probability or guaranteed yield.
6. Weather history is available for 14 districts for 2015-01-01 through 2025-12-31; the page labels it as historical gridded NASA POWER data, not a forecast.
7. Yield pages report actual historical records. A district/crop training mean can be loaded from the saved model bundle and is identified as a baseline reference.
8. Missing market prices/costs are surfaced rather than replaced by example predictions or fabricated prices.
9. Model performance uses saved metadata; limitations and the low soil-clustering data adequacy are presented.
10. The nine navigation pages were exercised in the browser in the integration check; mobile layout was also checked at 375 CSS pixels without horizontal body overflow.

## D. Main blockers and confirmed defects

| ID | Finding | Severity / priority |
|---|---|---|
| G-01 | `run_walk_forward_cv` raises `UnboundLocalError` for otherwise sufficient price records because `mean_absolute_error` is imported after it is used. Reproduced with a local fixture. | High / P1 |
| G-02 | The Data.gov.in fetcher returns a JSON path, but the pipeline then reads it as CSV; the automated price acquisition path is not correctly wired end-to-end. | High / P1 |
| G-03 | CSV validator accepts duplicate primary keys with warnings and treats the file as valid; it also accepts non-finite floats and truncates fractional values for integer columns. | High / P1 |
| G-04 | API POST recommendation error paths do not catch missing-data `RuntimeError`/`LookupError` as the corresponding GET route does. | Medium / P2 |
| G-05 | Profitability uses the latest available market quote and historical district yield without aligning dates or documenting inflation/harvest timing; no matching cost/price data currently exist to validate a real calculation. | Medium / P1 before enabling |
| G-06 | Registry recovery silently replaces a corrupt JSON registry with a fresh schema registry; writes are not atomic. | Medium / P2 |
| G-07 | Uploads and ingestion pipelines write active files and registry metadata without atomic promotion or concurrency locking. | Medium / P2 |
| G-08 | The server binds only to loopback, but has no authentication/CSRF token or origin check for mutation routes. Safe only for a trusted local, single-user context; not deployment-ready. | Medium / P1 before exposure |
| G-09 | Five of seven notebooks are empty files; dataset provenance and original experimental analysis are incomplete. | Medium / P2 |

See [BUGS_AND_RISKS.md](./BUGS_AND_RISKS.md) for evidence and reproduction notes.

## E. Data readiness

| Domain | Audited state |
|---|---|
| Crop requirements | 10 records, schema-valid; useful basic fields, but no temperature/rainfall thresholds, crop duration, nutrient requirements, or district calendar in this table. |
| Soil | 23 qualitative district/soil profiles across 13 districts, schema-valid; not laboratory measurements. No N/P/K, organic carbon measurement, electrical conductivity, or farm-level moisture data. |
| Soil-crop suitability | 230 derived comparisons, no duplicate keys; 50 estimated pH component values blank. It is a heuristic matrix, not observed outcomes or ML predictions. |
| Weather | 56,252 rows, schema-valid, exactly 4,018 rows per district and 14 districts, date range 2015-01-01–2025-12-31. Raw NASA POWER JSON files are present for all 14 districts. This audit did not make live network requests or independently verify the API source. |
| Crop yield | 6,422 schema-valid rows, 14 districts, 22 crops, 2001-02–2023-24. Every standardized record is labeled `Annual`; source column identifies DES Kerala. |
| Prices / cultivation costs / demand | Files exist at zero bytes; no usable records. No market-price forecast or profit estimate can be supported. |
| Crop calendar | No file; schema exists. |
| Crop risk | No separate risk dataset/schema or integrated risk engine was found. |

Full inventory is in [DATASET_AUDIT.md](./DATASET_AUDIT.md) and [DATASET_INVENTORY.csv](./DATASET_INVENTORY.csv).

## F. Machine-learning readiness

- **Soil clustering:** Saved KMeans model and metadata exist; 23 records, five ordinal-encoded categorical features, `k=5`, recorded silhouette 0.5849. Application inference was exercised. The cluster result is explicitly indicative. Ordinal codes create artificial distances between nominal categories, and the small sample limits interpretation.
- **Yield model:** Saved model bundle and metadata exist; time-aware train/test split recorded as 1,667 / 818 records, training years 2015-16 to 2020-21 and test years 2021-22 to 2023-24. Baseline district/crop mean has test MAE 1,168.11 kg/ha; Random Forest MAE 1,619.72 kg/ha and R² 0.8283; Ridge performs poorly. The saved baseline is loaded and tested; no weather-aware future inference is offered.
- **Price model:** No trained estimator or inference endpoint. Metadata explicitly defers modelling at zero records. In addition, the implemented walk-forward routine currently fails on sufficient records.

Detailed model evidence: [MODEL_AUDIT.md](./MODEL_AUDIT.md).

## G. Completion summary

Priority work is to repair and test price ingestion/forecasting and strengthen validation, acquire authentic market prices and cultivation costs, complete domain-specific calculation rules, and harden upload/server operations before any non-local exposure. The current app should be treated as a local decision-support prototype, not a production advisory service.

See [REMAINING_WORK.md](./REMAINING_WORK.md) for acceptance criteria and dependencies, [FEATURE_MATRIX.md](./FEATURE_MATRIX.md) for the full feature verification matrix, and [TEST_RESULTS.md](./TEST_RESULTS.md) for exact executed checks and limitations.
