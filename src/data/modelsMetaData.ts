export const MODELS_META = {
  soil: {
  "task": "soil_region_clustering",
  "algorithm": "KMeans",
  "k": 5,
  "silhouette": 0.5849,
  "agglomerative_silhouette": 0.5717234835856516,
  "n_records": 23,
  "n_features": 5,
  "feature_columns": [
    "soil_texture",
    "drainage",
    "ph_category",
    "organic_matter_category",
    "fertility_category"
  ],
  "data_adequacy": "LOW - 23 records, 5 categorical features. Results are indicative groupings only.",
  "interpretation_warning": "Cluster IDs are not quality rankings and must not be treated as ML predictions.",
  "saved_at": "2026-10-25T14:47:16.851189",
  "model_file": "models\\soil_clustering.joblib"
},
  yield: {
  "task": "crop_yield_prediction",
  "best_model": "baseline_district_crop_mean",
  "n_train": 1667,
  "n_test": 818,
  "train_years": "2015-16 to 2020-21",
  "test_years": "2021-22 to 2023-24",
  "feature_columns": [
    "crop_enc",
    "district_enc",
    "year_index",
    "annual_rainfall_mm",
    "mean_tmax_c",
    "mean_tmin_c",
    "mean_rh_percent"
  ],
  "metrics": {
    "baseline_district_crop_mean": {
      "mae": 1168.1055705986594,
      "rmse": 5033.047453777477,
      "r2": 0.8122917994750407,
      "mape": 14.219249270079004
    },
    "ridge_regression": {
      "mae": 6820.468111551033,
      "rmse": 11609.519369969448,
      "r2": 0.0012663630169628126,
      "mape": 1424.563784444024
    },
    "random_forest": {
      "mae": 1619.7178380336638,
      "rmse": 4814.202043667359,
      "r2": 0.8282606472237509,
      "mape": 36.70204488622992
    }
  },
  "feature_importances": {
    "crop_enc": 0.8044400102571778,
    "district_enc": 0.08027125558799307,
    "year_index": 0.008144595938556423,
    "annual_rainfall_mm": 0.05331865856996288,
    "mean_tmax_c": 0.012649827034892197,
    "mean_tmin_c": 0.03131420116421585,
    "mean_rh_percent": 0.009861451447201791
  },
  "data_adequacy": "MODERATE — 9 weather-joined agricultural years (2015-24). Model captures cross-crop and district differences but has limited temporal depth. Confidence intervals are wide; forecasts should be presented as indicative ranges.",
  "validation_design": "Time-aware split: test = 4 most recent agri-years; no random shuffle. Target leakage excluded: area and production not in feature set.",
  "saved_at": "2026-10-25T14:47:17.960302",
  "model_file": "models\\crop_yield_model.joblib"
},
  price: {
  "task": "market_price_forecasting",
  "status": "deferred_insufficient_data",
  "data_available": false,
  "record_count": 0,
  "reason": "market_prices.csv does not exist or is empty.",
  "threshold_records": 500,
  "threshold_months": 24,
  "planned_validation": "walk_forward_expanding_window",
  "planned_baseline": "seasonal_naive_lag12",
  "planned_models": [
    "Ridge",
    "GradientBoostedTrees"
  ],
  "error_unit": "INR/quintal",
  "data_source_url": "https://agmarknet.gov.in/PriceTrends/SA_Pri_Month.aspx",
  "upload_path": "data/raw/market_prices/",
  "template_path": "data/raw/market_prices/market_prices_template.csv"
}
};
