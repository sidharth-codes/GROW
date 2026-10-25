import { growService } from './growService';
import { CROP_CALENDAR_DATA, CropCalendarEntry } from '../data/cropCalendarData';
import { CULTIVATION_COST_BENCHMARKS, CropCostStructure } from '../data/cultivationCostData';
import {
  VERIFIED_MARKET_PRICES,
  KERALA_BASE_PRICES,
  RECENT_MARKET_ARRIVALS,
  VerifiedMarketPrice,
} from '../data/marketDataEnriched';
import {
  DISTRICT_SOIL_BENCHMARKS,
  evaluateFarmerSoilTest,
  SoilTestEvaluation,
} from '../data/soilMeasurementsData';

export type AreaUnit = 'acres' | 'hectares' | 'cents';

export interface FarmAreaConversion {
  raw_value: number;
  raw_unit: AreaUnit;
  in_hectares: number;
  in_acres: number;
  in_cents: number;
}

export function convertArea(value: number, unit: AreaUnit): FarmAreaConversion {
  let hectares = 0;
  if (unit === 'hectares') {
    hectares = value;
  } else if (unit === 'acres') {
    hectares = value * 0.40468564224;
  } else if (unit === 'cents') {
    hectares = value * 0.0040468564224;
  }

  const acres = hectares * 2.4710538147;
  const cents = acres * 100;

  return {
    raw_value: value,
    raw_unit: unit,
    in_hectares: Math.round(hectares * 10000) / 10000,
    in_acres: Math.round(acres * 1000) / 1000,
    in_cents: Math.round(cents * 10) / 10,
  };
}

export interface FarmAnalysisInputs {
  district: string;
  total_area: number;
  area_unit: AreaUnit;
  occupied_area?: number;
  selected_crop?: string;
  water_access: 'Rainfed' | 'Borewell / Well' | 'Canal Irrigation' | 'Drip / Sprinkler';
  soil_ph?: number | null;
  soil_nitrogen?: number | null;
  soil_phosphorus?: number | null;
  soil_potassium?: number | null;
  soil_organic_carbon?: number | null;
  soil_ec?: number | null;
  custom_cost_override_per_ha?: number | null;
  custom_price_override_per_quintal?: number | null;
  scenario_target_yield_kg_ha?: number | null;
}

export interface MarketComparisonOption {
  market: string;
  distance_km: number;
  modal_price: number;
  price_unit: string;
  gross_revenue_at_this_market: number;
  net_advantage_inr: number;
}

export interface SingleCropAnalysisResult {
  crop: string;
  calendar: CropCalendarEntry | null;
  cost_structure: CropCostStructure | null;
  area: FarmAreaConversion;
  suitability: {
    overall_score: number;
    soil_match_score: number;
    weather_match_score: number;
    season_match_score: number;
    water_match_score: number;
    verdict: 'Highly Suitable' | 'Moderately Suitable' | 'Marginal / Requires Amendments' | 'Not Recommended';
    reasons: string[];
    soil_test_evaluation: SoilTestEvaluation | null;
  };
  production: {
    yield_kg_per_hectare: number;
    total_production_kg: number;
    total_production_quintals: number;
    total_production_tonnes: number;
    yield_basis: string;
    uncertainty_range_kg_ha: [number, number];
  };
  economics: {
    cost_inr_per_hectare: number;
    total_cultivation_cost_inr: number;
    cost_breakdown: { category: string; cost_inr: number; share_percent: number; description: string }[];
    price_inr_per_quintal: number;
    price_source_label: string;
    price_date: string;
    price_verified: boolean;
    base_price_floor_inr_per_quintal: number | null;
    base_price_scheme: string | null;
    gross_revenue_inr: number;
    net_profit_inr: number;
    profit_per_acre_inr: number;
    profit_per_hectare_inr: number;
    roi_percent: number;
    break_even_price_inr_per_quintal: number;
    break_even_yield_kg_per_hectare: number;
    is_profitable: boolean;
  };
  market_analysis: {
    primary_market: string;
    nearby_markets: MarketComparisonOption[];
    recent_arrivals: { market: string; quantity: number; unit: string; date: string }[];
    demand_indicator: string;
  };
  risks: {
    pest_disease_risks: string[];
    climate_risks: string[];
    economic_risks: string[];
    mitigation_actions: string[];
  };
  recommendation_summary: string;
}

export interface LandAllocationItem {
  crop: string;
  allocated_area: number;
  allocated_unit: AreaUnit;
  percent_of_farm: number;
}

export interface MultiCropAllocationResult {
  total_farm_area_acres: number;
  allocations: {
    crop: string;
    area_acres: number;
    area_hectares: number;
    production_tonnes: number;
    cost_inr: number;
    revenue_inr: number;
    profit_inr: number;
  }[];
  aggregate_production_tonnes: number;
  aggregate_cost_inr: number;
  aggregate_revenue_inr: number;
  aggregate_net_profit_inr: number;
  aggregate_roi_percent: number;
}

class FarmAnalysisService {
  public analyzeCrop(inputs: FarmAnalysisInputs): SingleCropAnalysisResult {
    const { district, total_area, area_unit, selected_crop = 'Rice', water_access } = inputs;
    const availableArea = Math.max(0, total_area - (inputs.occupied_area || 0));
    const areaConv = convertArea(availableArea, area_unit);

    const calendar = CROP_CALENDAR_DATA.find((c) => c.crop === selected_crop) || null;
    const benchmarkCost = CULTIVATION_COST_BENCHMARKS[selected_crop] || null;
    const basePrice = KERALA_BASE_PRICES[selected_crop] || null;
    const districtBenchmark = DISTRICT_SOIL_BENCHMARKS[district] || null;

    // 1. Soil Test Evaluation
    let soilEval: SoilTestEvaluation | null = null;
    const effectivePh = inputs.soil_ph != null ? inputs.soil_ph : (districtBenchmark ? districtBenchmark.mean_ph : 5.5);
    soilEval = evaluateFarmerSoilTest(
      effectivePh,
      inputs.soil_nitrogen,
      inputs.soil_phosphorus,
      inputs.soil_potassium,
      inputs.soil_organic_carbon,
      inputs.soil_ec
    );

    // 2. Suitability Scoring
    let soilScore = 80;
    const reasons: string[] = [];

    if (calendar) {
      if (effectivePh >= calendar.ph_min && effectivePh <= calendar.ph_max) {
        soilScore = 95;
        reasons.push(`Soil pH (${effectivePh}) is within optimal tolerance for ${selected_crop} (${calendar.ph_min}-${calendar.ph_max}).`);
      } else if (effectivePh < calendar.ph_min) {
        soilScore = Math.max(30, 85 - (calendar.ph_min - effectivePh) * 35);
        reasons.push(`Soil pH (${effectivePh}) is more acidic than preferred (${calendar.ph_min}); agricultural lime required.`);
      } else {
        soilScore = Math.max(40, 85 - (effectivePh - calendar.ph_max) * 30);
        reasons.push(`Soil pH (${effectivePh}) is higher than preferred (${calendar.ph_max}).`);
      }
    }

    // Weather match
    let weatherScore = 85;
    try {
      const weather = growService.getWeather(district);
      const avgRainfall30 = weather.latest_30_day_average.rainfall_mm;
      if (calendar && calendar.water_requirement === 'High' && water_access === 'Rainfed' && avgRainfall30 < 2) {
        weatherScore -= 20;
        reasons.push('High water requirement crop under rainfed conditions during a dry period.');
      } else {
        reasons.push(`Climate and seasonal conditions in ${district} are supportive.`);
      }
    } catch {
      // Fallback
    }

    // Water match
    let waterScore = 90;
    if (water_access === 'Rainfed') {
      if (calendar?.water_requirement === 'High' || calendar?.water_requirement === 'Very High') {
        waterScore = 55;
        reasons.push('Supplementary irrigation is strongly recommended for peak yield.');
      }
    } else {
      waterScore = 95;
      reasons.push(`Assured water access via ${water_access} mitigates seasonal dry spells.`);
    }

    const overallSuitability = Math.round((soilScore * 0.45) + (weatherScore * 0.3) + (waterScore * 0.25));

    let verdict: SingleCropAnalysisResult['suitability']['verdict'] = 'Highly Suitable';
    if (overallSuitability < 45) {
      verdict = 'Not Recommended';
    } else if (overallSuitability < 65) {
      verdict = 'Marginal / Requires Amendments';
    } else if (overallSuitability < 85) {
      verdict = 'Moderately Suitable';
    }

    // 3. Yield & Production Calculation
    let yieldKgHa = 2800; // default baseline
    let yieldBasis = 'Kerala State Historical District Yield Baseline';

    if (inputs.scenario_target_yield_kg_ha && inputs.scenario_target_yield_kg_ha > 0) {
      yieldKgHa = inputs.scenario_target_yield_kg_ha;
      yieldBasis = 'Farmer User-Specified Scenario Yield';
    } else {
      try {
        const yieldHistory = growService.getYieldHistory(district, selected_crop);
        if (yieldHistory.estimate?.value_kg_per_hectare) {
          yieldKgHa = yieldHistory.estimate.value_kg_per_hectare;
          yieldBasis = `Held-out Model Training Mean (${yieldHistory.estimate.training_period})`;
        } else if (yieldHistory.records.length > 0) {
          const recent = yieldHistory.records[yieldHistory.records.length - 1];
          if (recent.yield_kg_per_hectare) {
            yieldKgHa = recent.yield_kg_per_hectare;
            yieldBasis = `DES Kerala ${recent.year} District Record`;
          }
        }
      } catch {
        // Fallback default
      }
    }

    // Scale yield to available area
    const totalProductionKg = Math.round(yieldKgHa * areaConv.in_hectares);
    const totalProductionQuintals = Math.round((totalProductionKg / 100) * 10) / 10;
    const totalProductionTonnes = Math.round((totalProductionKg / 1000) * 100) / 100;
    const uncertaintyRange: [number, number] = [
      Math.round(yieldKgHa * 0.85),
      Math.round(yieldKgHa * 1.15),
    ];

    // 4. Economics & Costs
    const baseCostPerHa = benchmarkCost ? benchmarkCost.total_cost_inr_per_hectare : 80000;
    const effectiveCostPerHa = inputs.custom_cost_override_per_ha && inputs.custom_cost_override_per_ha > 0
      ? inputs.custom_cost_override_per_ha
      : baseCostPerHa;

    const totalCost = Math.round(effectiveCostPerHa * areaConv.in_hectares);

    // Calculate scaled itemized breakdown
    const costBreakdown = (benchmarkCost ? benchmarkCost.breakdown : []).map((item) => ({
      category: item.category,
      cost_inr: Math.round(item.cost_inr_per_hectare * areaConv.in_hectares),
      share_percent: item.share_percent,
      description: item.description,
    }));

    // Price determination
    let modalPricePerQuintal = 3200;
    let priceSourceLabel = 'Market Wholesale Benchmark';
    let priceDate = new Date().toISOString().split('T')[0];
    let priceVerified = true;

    if (inputs.custom_price_override_per_quintal && inputs.custom_price_override_per_quintal > 0) {
      modalPricePerQuintal = inputs.custom_price_override_per_quintal;
      priceSourceLabel = 'Farmer Custom Scenario Selling Price';
      priceVerified = true;
    } else {
      const marketQuotes = VERIFIED_MARKET_PRICES.filter(
        (p) => p.district === district && p.crop === selected_crop
      );
      if (marketQuotes.length > 0) {
        modalPricePerQuintal = marketQuotes[0].modal_price;
        priceSourceLabel = `${marketQuotes[0].market} (${marketQuotes[0].variety || 'Modal'})`;
        priceDate = marketQuotes[0].date;
        priceVerified = marketQuotes[0].price_verified;
      } else {
        const anyQuotes = VERIFIED_MARKET_PRICES.filter((p) => p.crop === selected_crop);
        if (anyQuotes.length > 0) {
          modalPricePerQuintal = anyQuotes[0].modal_price;
          priceSourceLabel = `${anyQuotes[0].market} (Regional quote)`;
          priceDate = anyQuotes[0].date;
          priceVerified = anyQuotes[0].price_verified;
        } else if (basePrice) {
          modalPricePerQuintal = basePrice.base_price_inr_per_quintal;
          priceSourceLabel = basePrice.scheme_name;
          priceVerified = true;
        }
      }
    }

    // Revenue, Profit, Break-even
    // Gross revenue = Total Quintals * Price per Quintal
    const grossRevenue = Math.round(totalProductionQuintals * modalPricePerQuintal);
    const netProfit = grossRevenue - totalCost;
    const profitPerAcre = areaConv.in_acres > 0 ? Math.round(netProfit / areaConv.in_acres) : 0;
    const profitPerHectare = areaConv.in_hectares > 0 ? Math.round(netProfit / areaConv.in_hectares) : 0;
    const roiPercent = totalCost > 0 ? Math.round((netProfit / totalCost) * 100) : 0;

    // Break-even selling price (INR per quintal) = total cost / total quintals
    const breakEvenPrice = totalProductionQuintals > 0
      ? Math.round((totalCost / totalProductionQuintals) * 10) / 10
      : 0;

    // Break-even yield (kg/ha) = total cost per ha / (price per kg)
    const pricePerKg = modalPricePerQuintal / 100;
    const breakEvenYield = pricePerKg > 0 ? Math.round(effectiveCostPerHa / pricePerKg) : 0;

    // 5. Market Comparison
    const districtMarkets = VERIFIED_MARKET_PRICES.filter((p) => p.crop === selected_crop);
    const nearbyMarkets: MarketComparisonOption[] = districtMarkets.map((m) => {
      const revenueHere = Math.round(totalProductionQuintals * m.modal_price);
      return {
        market: `${m.market} (${m.district})`,
        distance_km: m.distance_km_from_district_center || 15,
        modal_price: m.modal_price,
        price_unit: m.price_unit,
        gross_revenue_at_this_market: revenueHere,
        net_advantage_inr: revenueHere - grossRevenue,
      };
    });

    const recentArrivals = RECENT_MARKET_ARRIVALS.filter(
      (a) => a.crop === selected_crop || a.district === district
    ).map((a) => ({
      market: a.market,
      quantity: a.arrival_quantity,
      unit: a.arrival_unit,
      date: a.date,
    }));

    // 6. Risks & Mitigations
    const pestRisks = calendar ? calendar.major_pests : ['General seasonal pests'];
    const diseaseRisks = calendar ? calendar.major_diseases : ['Leaf spot and root rot'];
    const climateRisks = calendar ? calendar.climate_vulnerabilities : ['Heavy rainfall during harvest'];

    const mitigations: string[] = [];
    if (soilEval.lime_recommendation_kg_per_ha > 0) {
      mitigations.push(`Incorporate agricultural lime @ ${soilEval.lime_recommendation_kg_per_ha} kg/ha to mitigate root toxicity.`);
    }
    mitigations.push('Adopt integrated pest management (IPM) using Trichoderma and neem seed kernel extract before peak monsoon.');
    if (basePrice) {
      mitigations.push(`Register on the Subhiksha Keralam / Supplyco portal to access the guaranteed base price floor of ₹${basePrice.base_price_inr_per_kg}/kg.`);
    }

    // Recommendation synthesis
    let recSummary = '';
    if (netProfit > 0 && overallSuitability >= 65) {
      recSummary = `${selected_crop} is a commercially sound and agronomically viable choice for your ${availableArea} ${area_unit} farm in ${district}. At an expected yield of ${yieldKgHa.toLocaleString()} kg/ha and prevailing modal price of ₹${modalPricePerQuintal.toLocaleString()}/quintal, an estimated net profit of ₹${netProfit.toLocaleString()} (₹${profitPerAcre.toLocaleString()}/acre) is projected with an estimated ROI of ${roiPercent}%.`;
    } else if (netProfit <= 0 && overallSuitability >= 65) {
      recSummary = `${selected_crop} is agronomically suitable for ${district}, but current market price (₹${modalPricePerQuintal}/quintal) sits near or below the break-even threshold of ₹${breakEvenPrice}/quintal. Consider processing/value-addition, exploring premium direct markets, or accessing the Kerala Base Price floor (₹${basePrice?.base_price_inr_per_kg || '—'}/kg) to guarantee positive returns.`;
    } else {
      recSummary = `${selected_crop} faces notable agronomic constraints in ${district} (Suitability score: ${overallSuitability}/100). Review the soil and water recommendations above, or compare alternative crops better matched to local conditions.`;
    }

    return {
      crop: selected_crop,
      calendar,
      cost_structure: benchmarkCost,
      area: areaConv,
      suitability: {
        overall_score: overallSuitability,
        soil_match_score: soilScore,
        weather_match_score: weatherScore,
        season_match_score: 90,
        water_match_score: waterScore,
        verdict,
        reasons,
        soil_test_evaluation: soilEval,
      },
      production: {
        yield_kg_per_hectare: yieldKgHa,
        total_production_kg: totalProductionKg,
        total_production_quintals: totalProductionQuintals,
        total_production_tonnes: totalProductionTonnes,
        yield_basis: yieldBasis,
        uncertainty_range_kg_ha: uncertaintyRange,
      },
      economics: {
        cost_inr_per_hectare: effectiveCostPerHa,
        total_cultivation_cost_inr: totalCost,
        cost_breakdown: costBreakdown,
        price_inr_per_quintal: modalPricePerQuintal,
        price_source_label: priceSourceLabel,
        price_date: priceDate,
        price_verified: priceVerified,
        base_price_floor_inr_per_quintal: basePrice ? basePrice.base_price_inr_per_quintal : null,
        base_price_scheme: basePrice ? basePrice.scheme_name : null,
        gross_revenue_inr: grossRevenue,
        net_profit_inr: netProfit,
        profit_per_acre_inr: profitPerAcre,
        profit_per_hectare_inr: profitPerHectare,
        roi_percent: roiPercent,
        break_even_price_inr_per_quintal: breakEvenPrice,
        break_even_yield_kg_per_hectare: breakEvenYield,
        is_profitable: netProfit > 0,
      },
      market_analysis: {
        primary_market: priceSourceLabel,
        nearby_markets: nearbyMarkets,
        recent_arrivals: recentArrivals,
        demand_indicator: 'Consistent Kerala Wholesale Mandi Inflow & Local Institutional Demand',
      },
      risks: {
        pest_disease_risks: pestRisks,
        climate_risks: climateRisks,
        economic_risks: [
          `Break-even price: ₹${breakEvenPrice}/quintal. If wholesale quotes drop below this level, gross margin becomes negative.`,
          'Labour wage inflation is the primary cost variable in Kerala (40-55% of total input cost).',
        ],
        mitigation_actions: mitigations,
      },
      recommendation_summary: recSummary,
    };
  }

  public compareCrops(district: string, areaValue: number, areaUnit: AreaUnit, cropList: string[]): SingleCropAnalysisResult[] {
    return cropList.map((crop) =>
      this.analyzeCrop({
        district,
        total_area: areaValue,
        area_unit: areaUnit,
        selected_crop: crop,
        water_access: 'Borewell / Well',
      })
    );
  }

  public calculateLandAllocation(
    totalArea: number,
    areaUnit: AreaUnit,
    district: string,
    allocations: { crop: string; percent: number }[]
  ): MultiCropAllocationResult {
    const totalAreaConv = convertArea(totalArea, areaUnit);

    const calculatedItems = allocations.map((alloc) => {
      const allocatedPortion = (totalArea * alloc.percent) / 100;
      const res = this.analyzeCrop({
        district,
        total_area: allocatedPortion,
        area_unit: areaUnit,
        selected_crop: alloc.crop,
        water_access: 'Borewell / Well',
      });

      return {
        crop: alloc.crop,
        area_acres: res.area.in_acres,
        area_hectares: res.area.in_hectares,
        production_tonnes: res.production.total_production_tonnes,
        cost_inr: res.economics.total_cultivation_cost_inr,
        revenue_inr: res.economics.gross_revenue_inr,
        profit_inr: res.economics.net_profit_inr,
      };
    });

    const aggregateProduction = calculatedItems.reduce((acc, curr) => acc + curr.production_tonnes, 0);
    const aggregateCost = calculatedItems.reduce((acc, curr) => acc + curr.cost_inr, 0);
    const aggregateRevenue = calculatedItems.reduce((acc, curr) => acc + curr.revenue_inr, 0);
    const aggregateProfit = aggregateRevenue - aggregateCost;
    const aggregateRoi = aggregateCost > 0 ? Math.round((aggregateProfit / aggregateCost) * 100) : 0;

    return {
      total_farm_area_acres: totalAreaConv.in_acres,
      allocations: calculatedItems,
      aggregate_production_tonnes: Math.round(aggregateProduction * 100) / 100,
      aggregate_cost_inr: aggregateCost,
      aggregate_revenue_inr: aggregateRevenue,
      aggregate_net_profit_inr: aggregateProfit,
      aggregate_roi_percent: aggregateRoi,
    };
  }
}

export const farmAnalysisService = new FarmAnalysisService();
