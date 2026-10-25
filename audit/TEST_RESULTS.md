# GROW Audit Test Results

**Date:** 2026-10-25  
**Execution environment:** Windows, Python 3.14.7 from the existing `.venv`, Node.js v24.21.0. Tests used local files; the price-model defect reproduction used generated in-memory rows only. No source data or model artifacts were rewritten.

## Executed checks

| Command / check | Result | Notes |
|---|---|---|
| `.venv\Scripts\python.exe -m unittest discover -s tests -v` | PASS — 39 tests | Dataset manager, ML metadata/utils, weather parser, ingestion normalizers, upload/recommendation HTTP workflow, missing-price behavior, and saved yield baseline. |
| `node --check app\frontend\app.js` | PASS | Frontend JavaScript parses. |
| Python in-memory `compile()` over all `.py` in `app/` and `tests/` | PASS | Syntax checked without generating bytecode files. |
| Dataset validator run over five non-empty processed CSVs | PASS | crops 10, soil 23, suitability v2 230, weather 56,252, yield 6,422; all valid; weather/yield/crops/soil have zero missing required values and zero duplicate keys; suitability has 50 optional pH blanks. |
| Dataset coverage scan using Python CSV reader | PASS | Weather 14×4,018 records, 2015-01-01–2025-12-31; yield 14 districts, 22 crops, 2001-02–2023-24; all yield seasons `Annual`. |
| Local model artifact inspection / baseline inference | PASS | `joblib` bundle keys inspected; saved baseline for Alappuzha/Banana was loaded through API service and test asserted returned model/period/value. |
| `run_walk_forward_cv` with generated adequate month-series fixture | FAIL as expected — defect reproduced | Raises `UnboundLocalError: cannot access local variable 'mean_absolute_error' where it is not associated with a value`. This is a confirmed price-CV defect. |
| Browser navigation of all nine pages | PASS (integration browser check) | Dashboard, recommendations, soil, weather, yield, market, profitability, datasets, and model performance rendered against local API; mobile viewport/body width check also run. |
| Local API health, static assets and main GET routes | PASS (integration smoke check) | Health, dashboard, recommendations, soil, weather, yield, market, profitability, datasets, and models returned HTTP 200 for the current data state. Empty-price/profitability responses were unavailable, not fake outputs. |
| Multipart invalid CSV upload | PASS (rejection) | HTTP 422 and schema errors returned; invalid file not promoted. |
| Notebook JSON inspection | PARTIAL | `01_data_collection.ipynb` and `07_recommendation_model.ipynb` parse; notebooks 02–06 are 0-byte files and fail JSON parsing. |
| `git diff --check` | PASS with line-ending warnings | Git reports LF→CRLF warnings for README and the two already-modified notebooks. No whitespace error reported. |

## Checks not performed

- No live NASA POWER or Data.gov.in/Agmarknet HTTP calls; source availability, credentials, rate limits, and present-day API compatibility remain unverified.
- No dependency vulnerability scanner, full accessibility audit, production load test, or deployment test was available/configured.
- No model retraining was run because it would write over saved artifacts.
- No profitability positive-case calculation could be verified because price and cost files contain zero bytes.
- No statistical validation of soil-crop suitability assumptions or soil-cluster agronomic meaning was attempted.
- Initial syntax command using wildcard arguments directly with `py_compile` failed because `py_compile` does not expand Windows wildcard arguments; it was replaced with the successful in-memory compile check above.

## Safety

Audit did not alter application code, data files, registry, model artifacts, or pre-existing uncommitted notebook content. Temporary upload/model tests used temporary directories or in-memory fixtures.
