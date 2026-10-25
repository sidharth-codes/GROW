# GROW Remaining Work and Execution Plan

Priorities are based on current verified blockers. Small/Medium/Large describes engineering effort, not calendar estimates. No application changes were made as part of this audit.

## Prioritized tasks

| ID | Task | Reason / dependency | Likely files | Acceptance criteria | Test required | Priority | Complexity |
|---|---|---|---|---|---|---|---|
| W-01 | Harden schema validation: duplicate keys, finite numeric values, integer exactness | Prevent corrupt/ambiguous uploads before enriching datasets; independent | `dataset_manager/validator.py`, `tests/test_dataset_manager.py` | Duplicate PK and NaN/±Infinity fail validation; `2.5` fails integer fields; clear row/column errors; valid existing files remain valid | Validator unit tests + real CSV schema tests | P1 | Small |
| W-02 | Repair market-price API JSON ingestion | Current fetcher/pipeline type mismatch means API path is not end-to-end functional | `price_ingestion/fetcher.py`, `price_ingestion/pipeline.py`, normalizer/tests | JSON fixture and CSV fixture both normalize to same canonical rows; malformed/empty API data never replace active data; errors visible | Offline fixture-based end-to-end ingestion test | P1 | Medium |
| W-03 | Fix walk-forward CV runtime failure | Required before any price modelling can run | `ml/price_model.py`, `tests/test_ml_modules.py` | Adequate synthetic temporal series completes folds and returns finite baseline/model MAE; insufficient series returns explicit reason | Unit test; no saved artifacts overwritten | P1 | Small |
| W-04 | Acquire authentic historical market prices | Price page, forecasting and profit blocked; requires authorized Agmarknet/Data.gov.in source export/API key | `data/raw/market_prices/`, price ingestion pipeline, registry | Verified source, location/date/crop/unit coverage; no template/example rows; schema-valid processed CSV with gap/duplicate report | Manual provenance review + validator + unit normalization tests | P1 | Large |
| W-05 | Define cost data and farmer input workflow | Profitability blocked by zero cost rows; user-provided values need source/reference year | `cultivation_cost` schema/data, Dataset UI/API, docs | Distinguish surveyed and farmer-entered cost; validate components vs total; store currency/year/district; no silent defaults | Known-value calculation and validation tests | P1 | Medium |
| W-06 | Specify and test profitability semantics | Existing code mixes most recent price with latest historical yield and lacks timing/real-vs-nominal rules | `api.py`, frontend profitability page, tests | Defines gross revenue, saleable quantity, costs, net margin, ROI (or explicitly omits ROI); aligns/labels source dates and market; tests kg↔q and loss cases | Calculation tests with hand-checked inputs and missing-data cases | P1 | Medium |
| W-07 | Secure mutation routes for intended deployment | Current local server has no auth/CSRF/origin checks; required before network exposure | `api.py`, frontend, deployment config/tests | Local-only behavior clearly documented or authenticated deployment; untrusted cross-origin upload blocked; upload size and errors controlled | Non-destructive security tests and deployment review | P1 | Medium |
| W-08 | Clarify suitability ranking across multiple soil profiles | Current default district view chooses best soil per crop, potentially hiding profile variability | `api.py`, recommendation UI, tests | UI shows selected profile or visibly identifies best-case; component reasons and coverage are clear | Multi-profile district fixture test + browser interaction | P2 | Small |
| W-09 | Improve soil clustering representation and stability checks | Nominal ordinal encoding with 23-row sample limits defensibility | `ml/soil_clustering.py`, `models/` retraining process, model tests | Encoding/distance rationale documented, stability tested, cluster labels not interpreted as quality; train artifact only after explicit user approval because it overwrites files | Reproducibility/stability evaluation with saved test output | P2 | Medium |
| W-10 | Extend soil/crop source data | Current soil is qualitative and partial; crop profiles omit many agronomic constraints | `schemas.py`, data files, source metadata | Separate measured soil samples from references; source-backed crop rainfall/temp/duration/nutrient data; missing values visible | Schema validation + provenance review | P2 | Large |
| W-11 | Add crop calendar and risk rules | No calendar file or risk system; recommendations omit timing and documented hazards | `crop_calendar` dataset, new risk service/page/UI, tests | Only source-supported seasons/rules shown; missing inputs produce unavailable warning, not fabricated risk | Rule-by-rule tests against documented references | P2 | Large |
| W-12 | Improve dataset lifecycle/registry writes | Registry silently reinitializes on corrupt JSON; file promotion can be interrupted or concurrent | `registry.py`, `ingestion.py`, all ingestion pipelines | Corrupt registry preserved with visible error; temp files atomically promoted; unique archive IDs; lock/conflict strategy | Failure-injection and concurrent upload tests in temp dirs | P2 | Medium |
| W-13 | Recover/retire empty notebooks; correct docs/dependency policy | Five notebook placeholders are invalid and README describes nonexistent frameworks | `README.md`, `requirements.txt`, `notebooks/` | README matches startup and actual stack; every retained notebook parses; dependencies and tested Python version documented | Fresh venv install/startup and notebook parse check | P2 | Small |
| W-14 | Add data freshness/provenance and API contract coverage | UI shows partial status but lacks per-dataset periods, validation summaries, and robust typed response contracts | `api.py`, `app.js`, tests, registry | Each dataset view exposes record/date/geography/source/validation timestamp; malformed API inputs have consistent JSON errors | API route/schema tests and browser accessibility pass | P2 | Medium |
| W-15 | Live external integration smoke tests | Current audit establishes code/raw artifacts, not present-day source endpoint availability | NASA/Data.gov.in test harness and documentation | Authorized small request checks parameters/status/schema; secrets from environment or protected input; no bulk download in test | Mock plus explicitly authorized live request | P2 | Medium |

## Recommended dependency-aware order

1. **W-01 validation** and **W-12 persistence safety** can proceed independently and should precede new uploads.
2. **W-02 API price normalization** and **W-03 CV repair** are independent code tasks; complete both before price evaluation.
3. **W-04 price acquisition** depends on a valid W-02 ingestion path and authorized source access. It can run alongside soil/crop source enrichment (W-10).
4. **W-05 costs** can be gathered independently; confirm source, year and unit before loading.
5. **W-06 profitability semantics** can be specified before data arrive, but numerical acceptance tests depend on W-04/W-05 and yield-data selection rules.
6. **W-07 security** is a gate before exposing the application beyond local loopback.
7. **W-08** improves recommendations now; **W-10/W-11** add more substantive inputs and must precede any expanded composite ranking.
8. **W-09** should be decided before retraining because model output files would be overwritten.
9. Finish with **W-13/W-14**, full test suite, clean setup verification, and only then deployment assessment.

## Not included in this audit

No task is marked done on the basis of the reports. No model retraining, external data collection, dependency installation, source-code fix, commit, push, or deployment was performed.
