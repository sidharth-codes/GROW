# GROW Model Audit

## Model inventory

| Model | Training data | Trained artifact exists | Training verified | Evaluation available | Inference tested | Status |
|---|---|---|---|---|---|---|
| Soil region clustering | 23 regional soil profiles; five categorical features | Yes: `models/soil_clustering.joblib` | Artifact loads and inference path is used; this audit did not retrain because training writes artifacts | Yes: KMeans silhouette 0.5849; agglomerative comparison 0.5717 | Yes, soil page/API path was exercised; no focused automated prediction assertion | PARTIAL — indicative only, low data adequacy |
| Crop yield | 2,485 weather-joined training/evaluation records (1,667 train, 818 test) from DES yield and weather inputs | Yes: `models/crop_yield_model.joblib` contains Random Forest, Ridge, scaler, encoder, and district/crop baseline means | Existing metadata and saved artifact inspected; training was not rerun because it overwrites model files | Yes: temporal split and model metrics in metadata | Yes: saved baseline for Alappuzha/Banana loaded and asserted; no Random Forest inference path is exposed | PARTIAL — historical baseline reference, not a farm forecast |
| Market price forecasting | None in current project data; 0 price records | No price estimator; metadata only | No; correctly deferred for insufficient data | No actual evaluation at present | No | BLOCKED by data; implementation routine also has a confirmed runtime defect |

## Soil clustering

- **Algorithm:** KMeans, with `k=5` selected by silhouette over `k=2..6`; random state 42 and `n_init=20`.
- **Features:** soil texture, drainage, qualitative pH category, organic-matter category, and fertility category.
- **Encoding:** project `OrdinalEncoder` assigns integer category indices based on appearance. KMeans then treats these indices as ordered/equidistant numeric values. This injects arbitrary geometry into nominal categories. `StandardScaler` is imported but not applied in the shown training path.
- **Target:** None; this is unsupervised grouping, not crop suitability or soil quality classification.
- **Evaluation:** silhouette 0.5849 for KMeans; 0.5717 agglomerative comparison, as recorded in `models/soil_clustering_meta.json`.
- **Persistence/inference:** model and encoder saved together; API loads the local artifact and predicts a group for a regional profile. Labels in UI are generic “Indicative soil group N”; metadata warns cluster IDs have no ranking meaning.
- **Limitations:** only 23 regional references, five categorical inputs, and 13 districts; no independent cluster stability or agronomic validation.

## Crop-yield model

- **Algorithm candidates:** district/crop historical-mean baseline, Ridge regression, Random Forest Regressor (`n_estimators=200`, `max_depth=8`, `min_samples_leaf=3`, `random_state=42`).
- **Inputs:** encoded crop, encoded district, agricultural start-year index, calendar-year district rainfall sum, and mean maximum/minimum temperature and relative humidity.
- **Target and units:** `yield_kg_per_hectare`.
- **Training/evaluation:** weather-joined source rows are split by agricultural year with the most recent four years in test; recorded train is 2015-16–2020-21 and test 2021-22–2023-24. No random shuffle. Stored split sizes sum to 2,485 records.
- **Stored metrics (held-out):**

| Candidate | MAE (kg/ha) | RMSE (kg/ha) | R² | MAPE |
|---|---:|---:|---:|---:|
| District/crop historical-mean baseline | 1,168.11 | 5,033.05 | 0.8123 | 14.22% |
| Ridge regression | 6,820.47 | 11,609.52 | 0.0013 | 1,424.56% |
| Random Forest | 1,619.72 | 4,814.20 | 0.8283 | 36.70% |

- Selection metadata identifies the baseline as best by MAE. Random Forest has a better R²/RMSE but worse MAE/MAPE, so “best” is metric-dependent and should remain explicit.
- `area_hectares` and `production_tonnes` are excluded from model features, avoiding direct target leakage from the ratio used to derive yield.
- The current API only serves the saved baseline mean for a crop/district pair, and it labels it as a training-period mean—not a forward forecast. The serialized Random Forest and Ridge estimators have no consumer inference endpoint.
- Limitations recorded in metadata: moderate adequacy, only nine weather-joined agriculture years, wide uncertainty, district averages, and limited temporal depth. No prediction interval is implemented.

## Market price model

- No real observations or trained model artifact exist; metadata reports `deferred_insufficient_data`, zero records, and thresholds of 500 records and 24 months.
- Planned approach is walk-forward expanding-window validation with seasonal-naive and Ridge baselines, but `run_walk_forward_cv` currently raises `UnboundLocalError`: it calls `mean_absolute_error` at line 149 before a local import at line 158. Reproduced locally with a temporary fixture; no project data were written.
- No forecast horizon, uncertainty interval, or inference implementation is available. Do not describe this as an operational price model.

## Reproducibility and recommended model actions

1. Fix the price-CV runtime failure and cover the first fold with a unit test.
2. Correct price ingestion/API response format before evaluating any price model.
3. Use authentic records; confirm monthly coverage, gaps, market/crop segmentation, units, and publication provenance.
4. Reassess categorical encoding for soil clustering and report cluster stability rather than a single silhouette alone.
5. If deploying a yield model, define inference-time weather semantics, unknown-category handling, confidence intervals, and temporal benchmark; retain the district/crop baseline as comparator.
