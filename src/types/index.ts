export const KERALA_DISTRICTS = [
  "Thiruvananthapuram",
  "Kollam",
  "Pathanamthitta",
  "Alappuzha",
  "Kottayam",
  "Idukki",
  "Ernakulam",
  "Thrissur",
  "Palakkad",
  "Malappuram",
  "Kozhikode",
  "Wayanad",
  "Kannur",
  "Kasaragod",
] as const;

export type KeralaDistrict = typeof KERALA_DISTRICTS[number];

export interface Crop {
  crop: string;
  preferred_soil_texture: string;
  preferred_drainage: string;
  preferred_ph_range: string;
  water_requirement: string;
  growing_season: string;
}

export interface SoilProfile {
  district: string;
  soil_type: string;
  soil_texture: string;
  drainage: string;
  soil_depth: string;
  ph_category: string;
  organic_matter_category: string;
  fertility_category: string;
}

export interface SuitabilityRecord {
  district: string;
  soil_type: string;
  crop: string;
  texture_score: number;
  drainage_score: number;
  estimated_ph_score: number | null;
  suitability_score: number;
  ph_status: string;
  score_method: string;
  interpretation?: string;
}

export interface WeatherObservation {
  district: string;
  date: string;
  rainfall_mm: number;
  temperature_min_c: number;
  temperature_max_c: number;
  humidity_percent: number;
  latitude: number;
  longitude: number;
  source: string;
}

export interface WeatherResponse {
  district: string;
  record_count: number;
  date_range: [string, string];
  latest_30_day_average: {
    rainfall_mm: number;
    temperature_min_c: number;
    temperature_max_c: number;
    humidity_percent: number;
  };
  observations: WeatherObservation[];
  provenance: string;
  limitations: string[];
}

export interface YieldRecord {
  year: string;
  district: string;
  crop: string;
  season?: string;
  area_hectares: number | null;
  production_tonnes: number | null;
  yield_kg_per_hectare: number | null;
  source?: string;
}

export interface YieldEstimate {
  value_kg_per_hectare: number;
  model: string;
  training_period: string;
  held_out_metrics: {
    mae: number;
    rmse: number;
    r2: number;
    mape: number;
  };
  interpretation: string;
}

export interface YieldResponse {
  records: YieldRecord[];
  total_matching_records: number;
  filters: {
    district: string | null;
    crop: string | null;
  };
  estimate: YieldEstimate | null;
  estimate_error: string | null;
  provenance: string;
  limitations: string[];
  model: any;
}

export interface MarketPriceRecord {
  date: string;
  district: string;
  market: string;
  crop: string;
  variety?: string;
  min_price: number;
  max_price: number;
  modal_price: number;
  price_unit: string;
  source?: string;
}

export interface MarketPriceResponse {
  available: boolean;
  records: MarketPriceRecord[];
  record_count: number;
  reason: string | null;
  price_unit_verified: boolean;
  price_unit_notice: string | null;
  provenance: string;
  requirements?: {
    minimum_records: number;
    minimum_months: number;
  };
  model?: any;
}

export interface ProfitabilityResponse {
  available: boolean;
  district?: string;
  crop?: string;
  yield_kg_per_hectare?: number;
  price_inr_per_quintal?: number;
  price_date?: string;
  cost_inr_per_hectare?: number;
  gross_revenue_inr_per_hectare?: number;
  indicative_margin_inr_per_hectare?: number;
  demand_records?: number;
  provenance?: string[];
  limitations?: string[];
  reason?: string;
  missing_inputs?: string[];
  cost_data_records?: number;
  price_data_records?: number;
  demand_data_records?: number;
}

export interface ColumnDef {
  name: string;
  dtype: 'string' | 'float' | 'integer' | 'date' | 'range';
  required?: boolean;
  description?: string;
  unit?: string | null;
  min_value?: number | null;
  max_value?: number | null;
  allowed_values?: string[];
}

export interface DatasetItem {
  dataset_id: string;
  name: string;
  category: string;
  description: string;
  status: string;
  source_info: {
    organization: string;
    source_url: string;
    download_method: string;
    api_endpoint?: string | null;
    manual_page_url?: string | null;
    manual_export_instructions?: string | null;
    expected_filename: string;
    expected_format?: string;
    license_or_terms?: string;
  };
  file_available: boolean;
  active_path: string | null;
  record_count: number;
  column_count: number;
  columns?: ColumnDef[];
  primary_key?: string[];
  validation_status: string;
  data_quality_limitations?: string[];
}

export interface DashboardResponse {
  as_of: string;
  metrics: {
    districts_covered: number;
    crops_catalogued: number;
    suitability_records: number;
    weather_records: number;
    yield_records: number;
    price_records: number;
    market_arrival_records: number;
    state_cost_summary_records: number;
    state_cost_a_records: number;
    datasets_available: number;
    datasets_total: number;
  };
  weather_latest_date: string | null;
  weather_source: string | null;
  models: {
    soil: any;
    yield: any;
    price: any;
  };
  data_gaps: string[];
  limitations: string[];
}

export type PageId =
  | 'analyze'
  | 'dashboard'
  | 'recommendations'
  | 'soil'
  | 'weather'
  | 'yield'
  | 'market'
  | 'profitability'
  | 'datasets'
  | 'models';
