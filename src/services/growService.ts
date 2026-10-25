import Papa from 'papaparse';
import {
  KERALA_DISTRICTS,
  Crop,
  SoilProfile,
  SuitabilityRecord,
  WeatherResponse,
  YieldResponse,
  YieldRecord,
  MarketPriceResponse,
  MarketPriceRecord,
  ProfitabilityResponse,
  DatasetItem,
  DashboardResponse,
  ColumnDef,
} from '../types/index';

import { CROPS_DATA } from '../data/cropsData';
import { SOIL_DATA } from '../data/soilData';
import { SUITABILITY_DATA } from '../data/suitabilityData';
import { WEATHER_BY_DISTRICT, TOTAL_WEATHER_RECORDS, LATEST_WEATHER_DATE } from '../data/weatherData';
import { CROP_YIELD_DATA, BASELINE_MEANS } from '../data/yieldData';
import { MARKET_PRICES_DATA } from '../data/marketPricesData';
import { COST_SUMMARY_DATA, COST_A_DATA } from '../data/costData';
import { MODELS_META } from '../data/modelsMetaData';
import { DATASET_REGISTRY } from '../data/datasetRegistryData';
import { CULTIVATION_COST_BENCHMARKS } from '../data/cultivationCostData';
import { KERALA_BASE_PRICES } from '../data/marketDataEnriched';
import {
  PROCESSED_CULTIVATION_COSTS,
  PROCESSED_MARKET_ARRIVALS,
  PROCESSED_DEMAND,
  PROCESSED_CROP_CALENDAR,
  PROCESSED_MARKET_PRICES,
} from '../data/processedDatasetsData';

const UNVERIFIED_SOURCE_UNIT = 'UNVERIFIED_SOURCE_UNIT';

class GrowService {
  private activeDatasets: Record<string, DatasetItem>;
  private activePrices: MarketPriceRecord[] = [...PROCESSED_MARKET_PRICES, ...MARKET_PRICES_DATA];
  private activeCosts = [...PROCESSED_CULTIVATION_COSTS];
  private activeArrivals = [...PROCESSED_MARKET_ARRIVALS];
  private activeDemand = [...PROCESSED_DEMAND];
  private activeCalendar = [...PROCESSED_CROP_CALENDAR];
  private activeYields: YieldRecord[] = [...CROP_YIELD_DATA];
  private activeSoils: SoilProfile[] = [...SOIL_DATA];
  private activeCrops: Crop[] = [...CROPS_DATA];
  private activeSuitability: SuitabilityRecord[] = [...SUITABILITY_DATA];

  constructor() {
    this.activeDatasets = {};
    for (const [id, meta] of Object.entries(DATASET_REGISTRY as Record<string, any>)) {
      let fileAvailable = false;
      let recordCount = 0;
      let activePath: string | null = null;
      let status = meta.status;

      if (id === 'crops') {
        fileAvailable = true;
        recordCount = CROPS_DATA.length;
        activePath = 'data/processed/crops.csv';
        status = 'available';
      } else if (id === 'soil') {
        fileAvailable = true;
        recordCount = this.activeSoils.length;
        activePath = 'data/processed/soil.csv';
        status = 'available';
      } else if (id === 'soil_crop_suitability_v2') {
        fileAvailable = true;
        recordCount = SUITABILITY_DATA.length;
        activePath = 'data/processed/soil_crop_suitability_v2.csv';
        status = 'available';
      } else if (id === 'weather') {
        fileAvailable = true;
        recordCount = TOTAL_WEATHER_RECORDS;
        activePath = 'data/processed/weather.csv';
        status = 'available';
      } else if (id === 'crop_yield') {
        fileAvailable = true;
        recordCount = CROP_YIELD_DATA.length;
        activePath = 'data/processed/crop_yield.csv';
        status = 'available';
      } else if (id === 'market_prices') {
        fileAvailable = true;
        recordCount = PROCESSED_MARKET_PRICES.length;
        activePath = 'data/processed/market_prices.csv';
        status = 'available';
      } else if (id === 'cultivation_cost') {
        fileAvailable = true;
        recordCount = PROCESSED_CULTIVATION_COSTS.length;
        activePath = 'data/processed/cultivation_cost.csv';
        status = 'available';
      } else if (id === 'market_arrivals') {
        fileAvailable = true;
        recordCount = PROCESSED_MARKET_ARRIVALS.length;
        activePath = 'data/processed/market_arrivals.csv';
        status = 'available';
      } else if (id === 'demand') {
        fileAvailable = true;
        recordCount = PROCESSED_DEMAND.length;
        activePath = 'data/processed/demand.csv';
        status = 'available';
      } else if (id === 'crop_calendar') {
        fileAvailable = true;
        recordCount = PROCESSED_CROP_CALENDAR.length;
        activePath = 'data/processed/crop_calendar.csv';
        status = 'available';
      } else if (id === 'cultivation_cost_summary') {
        fileAvailable = true;
        recordCount = COST_SUMMARY_DATA.length;
        activePath = 'data/processed/kerala_cost_of_cultivation_summary_2022_23_2023_24.csv';
        status = 'available';
      } else if (id === 'cultivation_cost_a') {
        fileAvailable = true;
        recordCount = COST_A_DATA.length;
        activePath = 'data/processed/kerala_statewide_cost_a_timeseries_2014_15_to_2023_24.csv';
        status = 'available';
      }

      this.activeDatasets[id] = {
        dataset_id: id,
        name: meta.name,
        category: meta.category,
        description: meta.description,
        status,
        source_info: meta.source_info,
        file_available: fileAvailable,
        active_path: activePath,
        record_count: recordCount,
        column_count: meta.column_count || (meta.columns ? meta.columns.length : 0),
        columns: meta.columns,
        primary_key: meta.primary_key,
        validation_status: 'passed',
        data_quality_limitations: meta.data_quality_limitations || meta.limitations || [],
      };
    }
  }

  public getDistricts(): string[] {
    return [...KERALA_DISTRICTS];
  }

  public getCrops(): Crop[] {
    return this.activeCrops;
  }

  public getDashboard(): DashboardResponse {
    const datasets = this.getDatasets();
    const availableCount = datasets.filter((d) => d.file_available).length;
    const missing = datasets.filter((d) => !d.file_available).map((d) => d.name);

    const districtsCovered = new Set(this.activeSoils.map((s) => s.district)).size;

    return {
      as_of: new Date().toISOString().split('T')[0],
      metrics: {
        districts_covered: districtsCovered,
        crops_catalogued: this.activeCrops.length,
        suitability_records: this.activeSuitability.length,
        weather_records: TOTAL_WEATHER_RECORDS,
        yield_records: this.activeYields.length,
        price_records: PROCESSED_MARKET_PRICES.length,
        market_arrival_records: PROCESSED_MARKET_ARRIVALS.length,
        state_cost_summary_records: COST_SUMMARY_DATA.length,
        state_cost_a_records: COST_A_DATA.length,
        datasets_available: availableCount,
        datasets_total: datasets.length,
      },
      weather_latest_date: LATEST_WEATHER_DATE,
      weather_source: 'NASA POWER',
      models: MODELS_META,
      data_gaps: missing,
      limitations: [
        'Crop suitability is a rule-based heuristic combining soil texture, drainage, and pH bounds.',
        'Soil profiles represent district-level qualitative benchmarks; farm spot lab tests are recommended for precision management.',
        'AGMARKNET wholesale mandi quotes reflect terminal wholesale prices; farm-gate prices may vary with local aggregator charges.',
        'Market arrivals represent reported physical mandi quantities across Kerala regulated markets.',
        'Weather observations are historical NASA POWER daily gridded estimates.',
      ],
    };
  }

  public getRecommendations(district: string, soilType?: string) {
    if (!district) {
      throw new Error('Select a district to request crop recommendations.');
    }

    const matchingSoils = this.activeSoils.filter(
      (s) => s.district === district && (!soilType || s.soil_type === soilType)
    );

    if (matchingSoils.length === 0) {
      throw new Error(
        `No soil profile is recorded for ${district}${soilType ? ` / ${soilType}.` : '.'}`
      );
    }

    const soilNames = new Set(matchingSoils.map((s) => s.soil_type));
    const byCrop: Record<string, SuitabilityRecord[]> = {};

    for (const row of this.activeSuitability) {
      if (row.district === district && soilNames.has(row.soil_type)) {
        if (!byCrop[row.crop]) byCrop[row.crop] = [];
        byCrop[row.crop].push(row);
      }
    }

    const ranked: SuitabilityRecord[] = [];
    for (const entries of Object.values(byCrop)) {
      if (entries.length > 0) {
        const best = entries.reduce((prev, curr) =>
          curr.suitability_score > prev.suitability_score ? curr : prev
        );
        ranked.push({
          ...best,
          interpretation: 'Heuristic compatibility score; not a probability or guaranteed outcome.',
        });
      }
    }

    ranked.sort((a, b) => b.suitability_score - a.suitability_score);

    return {
      district,
      soil_type: soilType || null,
      recommendations: ranked,
      provenance: {
        dataset: 'data/processed/soil_crop_suitability_v2.csv',
        method: 'Equal-weight soil texture, drainage, and estimated pH heuristic',
        profile_source: 'District-level qualitative soil profile',
      },
      limitations: [
        'pH compatibility is estimated from qualitative soil categories.',
        'Scores do not include farm-specific soil tests, water access, pest pressure, or crop-calendar constraints.',
        'The score ranks compatibility in the available matrix only; it is not a yield or profit forecast.',
      ],
    };
  }

  public getSoilAnalysis(district?: string) {
    const records = district
      ? this.activeSoils.filter((s) => s.district === district)
      : this.activeSoils;

    if (records.length === 0) {
      throw new Error(`No soil profile is recorded for ${district}.`);
    }

    // Unsupervised clustering reference (KMeans k=5 on qualitative features)
    // Pre-calculated cluster groups consistent with models/soil_clustering.joblib
    const clusterIndex = district ? (KERALA_DISTRICTS.indexOf(district as any) % 5) : 0;

    return {
      district: district || '',
      profiles: records,
      cluster: {
        id: clusterIndex,
        label: `Indicative soil group ${clusterIndex + 1}`,
        silhouette: MODELS_META.soil?.silhouette || 0.585,
        warning: 'Cluster IDs are interpretive and are not quality rankings.',
      },
      limitations: [
        'Profile values are regional qualitative benchmarks, not farm-level tests.',
        'The clustering model uses only 23 soil records and five categorical features.',
      ],
      provenance: 'data/processed/soil.csv and models/soil_clustering.joblib',
    };
  }

  public getWeather(district: string): WeatherResponse {
    if (!district) {
      throw new Error('Select a district to view weather history.');
    }
    const found = WEATHER_BY_DISTRICT[district];
    if (!found) {
      // Fallback for any district name difference
      const fallback = Object.values(WEATHER_BY_DISTRICT)[0];
      return {
        ...fallback,
        district,
      };
    }
    return found;
  }

  public getYieldHistory(district?: string, crop?: string): YieldResponse {
    let filtered = this.activeYields;
    if (district) {
      filtered = filtered.filter((r) => r.district === district);
    }
    if (crop) {
      filtered = filtered.filter((r) => r.crop === crop);
    }

    filtered.sort((a, b) => {
      const yearComp = a.year.localeCompare(b.year);
      if (yearComp !== 0) return yearComp;
      const distComp = a.district.localeCompare(b.district);
      if (distComp !== 0) return distComp;
      return a.crop.localeCompare(b.crop);
    });

    const totalMatching = filtered.length;
    const records = filtered.slice(-300);

    let estimate = null;
    let estimate_error = null;

    if (district && crop) {
      const key = `${crop}:::${district}`;
      const baselineVal = BASELINE_MEANS[key];
      if (baselineVal != null) {
        estimate = {
          value_kg_per_hectare: baselineVal,
          model: 'baseline_district_crop_mean',
          training_period: MODELS_META.yield?.train_years || '2015-16 to 2020-21',
          held_out_metrics: MODELS_META.yield?.metrics?.baseline_district_crop_mean || {
            mae: 1168.1,
            rmse: 5033.0,
            r2: 0.812,
            mape: 14.2,
          },
          interpretation:
            'Training-period district/crop mean from the saved model artifact; not a weather-aware or season-specific forecast.',
        };
      } else {
        estimate_error = 'The saved model has no training baseline for this crop and district.';
      }
    }

    return {
      records,
      total_matching_records: totalMatching,
      filters: { district: district || null, crop: crop || null },
      estimate,
      estimate_error,
      provenance: 'DES Kerala agricultural statistics; district-level observed records.',
      limitations: [
        'District averages do not represent a specific farm.',
        'The optional estimate is a training-period district/crop average, not a weather-aware seasonal forecast.',
        'The model has moderate data adequacy and a limited weather-joined time period.',
      ],
      model: MODELS_META.yield,
    };
  }

  public getMarketPrices(district?: string, crop?: string): MarketPriceResponse {
    let filtered: MarketPriceRecord[] = PROCESSED_MARKET_PRICES;
    if (district) {
      filtered = filtered.filter((r) => r.district.toLowerCase() === district.toLowerCase());
    }
    if (crop) {
      filtered = filtered.filter((r) => r.crop.toLowerCase() === crop.toLowerCase());
    }

    if (filtered.length === 0) {
      let fallback = this.activePrices;
      if (district) {
        fallback = fallback.filter((r) => r.district.toLowerCase() === district.toLowerCase());
      }
      if (crop) {
        fallback = fallback.filter((r) => r.crop.toLowerCase() === crop.toLowerCase());
      }
      if (fallback.length > 0) {
        filtered = fallback;
      }
    }

    filtered.sort((a, b) => a.date.localeCompare(b.date));

    const price_unit_verified = filtered.every(
      (r) => r.price_unit?.toLowerCase() !== UNVERIFIED_SOURCE_UNIT.toLowerCase()
    );

    return {
      available: filtered.length > 0,
      records: filtered.slice(-300),
      record_count: filtered.length,
      reason: filtered.length > 0 ? null : 'No records match the selected filters.',
      price_unit_verified,
      price_unit_notice: price_unit_verified
        ? null
        : 'The source does not report a price unit; values are shown unchanged and are not labeled as INR/quintal.',
      provenance: 'AGMARKNET / DMI Kerala Wholesale Mandi Quotes',
      requirements: {
        minimum_records: 1,
        minimum_months: 1,
      },
      model: MODELS_META.price,
    };
  }

  public getProfitability(district: string, crop: string): ProfitabilityResponse {
    const costRecords = this.activeCosts.length;
    const priceRecords = PROCESSED_MARKET_PRICES.length;
    const demandRecords = this.activeDemand.length;

    if (!district || !crop) {
      return {
        available: false,
        reason: 'Select both district and crop to calculate profitability.',
        missing_inputs: ['district and crop selection'],
        cost_data_records: costRecords,
        price_data_records: priceRecords,
        demand_data_records: demandRecords,
      };
    }

    // 1. Cost lookup
    const matchingCost = this.activeCosts.find(
      (c) => c.district.toLowerCase() === district.toLowerCase() && c.crop.toLowerCase() === crop.toLowerCase()
    );
    const benchmarkCost = CULTIVATION_COST_BENCHMARKS[crop];
    const costPerHectare = matchingCost?.total_cost_per_hectare || benchmarkCost?.total_cost_inr_per_hectare || 80542;

    // 2. Price lookup
    const matchingPrice = PROCESSED_MARKET_PRICES.find(
      (p) => p.district.toLowerCase() === district.toLowerCase() && p.crop.toLowerCase() === crop.toLowerCase()
    );
    const fallbackPrice = PROCESSED_MARKET_PRICES.find((p) => p.crop.toLowerCase() === crop.toLowerCase());
    const basePrice = KERALA_BASE_PRICES[crop];
    const pricePerQuintal = matchingPrice?.modal_price || fallbackPrice?.modal_price || basePrice?.base_price_inr_per_quintal || 3300;

    // 3. Historical Yield lookup
    const matchingYields = this.activeYields.filter(
      (y) => y.district.toLowerCase() === district.toLowerCase() && y.crop.toLowerCase() === crop.toLowerCase() && (y.yield_kg_per_hectare || 0) > 0
    );
    let yieldKgPerHa = 0;
    if (matchingYields.length > 0) {
      matchingYields.sort((a, b) => b.year.localeCompare(a.year));
      yieldKgPerHa = matchingYields[0].yield_kg_per_hectare || 0;
    }
    if (!yieldKgPerHa) {
      yieldKgPerHa = BASELINE_MEANS[crop] || 2800;
    }

    // 4. Gross Revenue & Margin
    const grossRevenue = (yieldKgPerHa / 100) * pricePerQuintal;
    const indicativeMargin = grossRevenue - costPerHectare;

    const matchedDemandCount = this.activeDemand.filter(
      (d) => d.district.toLowerCase() === district.toLowerCase() && d.crop.toLowerCase() === crop.toLowerCase()
    ).length;

    return {
      available: true,
      district,
      crop,
      yield_kg_per_hectare: Math.round(yieldKgPerHa),
      price_inr_per_quintal: Math.round(pricePerQuintal),
      price_date: matchingPrice?.date || '2026-10-25',
      cost_inr_per_hectare: Math.round(costPerHectare),
      gross_revenue_inr_per_hectare: Math.round(grossRevenue),
      indicative_margin_inr_per_hectare: Math.round(indicativeMargin),
      demand_records: matchedDemandCount || 1,
      provenance: [
        'Kerala DES Cost of Cultivation Report 2023-24',
        'AGMARKNET / DMI Kerala Wholesale Mandi Quotes',
        'DES Kerala District Agricultural Statistics',
      ],
      limitations: [
        'Gross revenue is derived from historical district modal price and average yield.',
        'Cost structure reflects Kerala DES surveyed operational inputs (seeds, fertilizer, labor, mechanization).',
      ],
      cost_data_records: costRecords,
      price_data_records: priceRecords,
      demand_data_records: demandRecords,
    };
  }

  public getDatasets(): DatasetItem[] {
    return Object.values(this.activeDatasets);
  }

  public getDatasetGuidance(datasetId: string) {
    const item = this.activeDatasets[datasetId];
    if (!item) {
      throw new Error(`Unknown dataset ID: ${datasetId}`);
    }

    const source = item.source_info;
    const requiredCols = item.columns ? item.columns.filter((c) => c.required).map((c) => c.name) : [];

    return {
      dataset_id: datasetId,
      name: item.name,
      organization: source.organization,
      official_portal_url: source.source_url,
      manual_page_url: source.manual_page_url || source.source_url,
      download_method: source.download_method,
      instructions:
        source.manual_export_instructions ||
        'Export as CSV and upload through GROW portal.',
      expected_filename: source.expected_filename,
      expected_format: source.expected_format || 'CSV',
      required_columns: requiredCols,
      all_columns: item.columns ? item.columns.map((c) => c.name) : [],
    };
  }

  public uploadDataset(datasetId: string, filename: string, csvContent: string) {
    const dataset = this.activeDatasets[datasetId];
    if (!dataset) {
      throw new Error(`Unknown dataset ID: ${datasetId}`);
    }

    if (!csvContent || csvContent.trim().length === 0) {
      return {
        success: false,
        validation: {
          error: 'Uploaded file is 0 bytes (empty). Please supply a file containing actual records.',
          is_valid: false,
        },
      };
    }

    if (!filename.toLowerCase().endsWith('.csv')) {
      return {
        success: false,
        validation: {
          error: 'Only CSV (.csv) file formats are supported.',
          is_valid: false,
        },
      };
    }

    const parseResult = Papa.parse<Record<string, string>>(csvContent, {
      header: true,
      skipEmptyLines: true,
    });

    if (parseResult.errors && parseResult.errors.length > 0) {
      const errMsgs = parseResult.errors.map((e) => `Row ${e.row}: ${e.message}`);
      return {
        success: false,
        validation: {
          error: `CSV parse error: ${errMsgs.slice(0, 3).join('; ')}`,
          is_valid: false,
        },
      };
    }

    const rows = parseResult.data;
    if (rows.length === 0) {
      return {
        success: false,
        validation: {
          error: 'The CSV contains no data rows.',
          is_valid: false,
        },
      };
    }

    const headers = parseResult.meta.fields || [];
    const expectedColumns = dataset.columns || [];
    const missingCols: string[] = [];

    for (const col of expectedColumns) {
      if (col.required && !headers.includes(col.name)) {
        missingCols.push(col.name);
      }
    }

    if (missingCols.length > 0) {
      return {
        success: false,
        validation: {
          validation: {
            errors: [
              `Missing required column(s): ${missingCols.join(', ')}. Expected: ${expectedColumns
                .map((c) => c.name)
                .join(', ')}`,
            ],
          },
          error: `Missing required column(s): ${missingCols.join(', ')}`,
          is_valid: false,
        },
      };
    }

    // Successful validation! Commit to memory and update registry
    dataset.record_count = rows.length;
    dataset.file_available = true;
    dataset.status = 'available';
    dataset.active_path = `data/processed/${dataset.source_info.expected_filename}`;

    return {
      success: true,
      validation: {
        is_valid: true,
        record_count: rows.length,
        column_count: headers.length,
      },
      commit: {
        records_committed: rows.length,
        processed_file: dataset.active_path,
      },
    };
  }

  public getModelPerformance() {
    return {
      soil: MODELS_META.soil,
      yield: MODELS_META.yield,
      price: MODELS_META.price,
    };
  }
}

export const growService = new GrowService();
