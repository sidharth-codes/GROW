import { convertArea, farmAnalysisService } from '../src/services/farmAnalysisService';
import { evaluateFarmerSoilTest } from '../src/data/soilMeasurementsData';
import { CULTIVATION_COST_BENCHMARKS } from '../src/data/cultivationCostData';
import { KERALA_BASE_PRICES } from '../src/data/marketDataEnriched';
import fs from 'fs';
import path from 'path';

function assert(condition: boolean, message: string) {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

function runTests() {
  console.log('Running GROW Farm Analysis Test Suite...\n');

  // Test 1: Area Conversion
  console.log('Test 1: Area Conversion (Acres, Hectares, Cents)');
  const acreConv = convertArea(1, 'acres');
  assert(Math.abs(acreConv.in_hectares - 0.4047) < 0.001, '1 acre should equal approx 0.4047 hectares');
  assert(Math.abs(acreConv.in_cents - 100) < 0.1, '1 acre should equal 100 cents');

  const haConv = convertArea(1, 'hectares');
  assert(Math.abs(haConv.in_acres - 2.471) < 0.01, '1 hectare should equal approx 2.471 acres');
  assert(Math.abs(haConv.in_cents - 247.1) < 0.5, '1 hectare should equal approx 247.1 cents');

  const centConv = convertArea(50, 'cents');
  assert(Math.abs(centConv.in_acres - 0.5) < 0.001, '50 cents should equal 0.5 acres');
  console.log('✓ Area conversion passed.\n');

  // Test 2: Production Calculation (kg, quintals, tonnes)
  console.log('Test 2: Yield to Total Production Calculation');
  const resultPaddy = farmAnalysisService.analyzeCrop({
    district: 'Palakkad',
    total_area: 2.47105,
    area_unit: 'acres', // exactly 1.0 hectare
    selected_crop: 'Rice',
    water_access: 'Borewell / Well',
    scenario_target_yield_kg_ha: 3000,
  });

  assert(resultPaddy.production.total_production_kg === 3000, '1 ha at 3000 kg/ha should yield 3000 kg');
  assert(resultPaddy.production.total_production_quintals === 30, '3000 kg should equal 30 quintals');
  assert(resultPaddy.production.total_production_tonnes === 3.0, '3000 kg should equal 3.0 tonnes');
  console.log('✓ Yield to production calculation passed.\n');

  // Test 3: Revenue, Cost, Profit, Break-Even Targets
  console.log('Test 3: Economics, Net Profit & Break-Even Formulas');
  const customAnalysis = farmAnalysisService.analyzeCrop({
    district: 'Palakkad',
    total_area: 1.0,
    area_unit: 'hectares',
    selected_crop: 'Rice',
    water_access: 'Borewell / Well',
    scenario_target_yield_kg_ha: 3000,
    custom_cost_override_per_ha: 60000,
    custom_price_override_per_quintal: 3000, // ₹30/kg
  });

  // Gross Revenue = 30 quintals * ₹3000 = ₹90,000
  assert(customAnalysis.economics.gross_revenue_inr === 90000, `Expected gross revenue ₹90,000, got ${customAnalysis.economics.gross_revenue_inr}`);
  // Net Profit = ₹90,000 - ₹60,000 = ₹30,000
  assert(customAnalysis.economics.net_profit_inr === 30000, `Expected net profit ₹30,000, got ${customAnalysis.economics.net_profit_inr}`);
  // ROI = (30000 / 60000) * 100 = 50%
  assert(customAnalysis.economics.roi_percent === 50, `Expected ROI 50%, got ${customAnalysis.economics.roi_percent}%`);
  // Break-even selling price = ₹60,000 / 30 quintals = ₹2,000 / quintal
  assert(customAnalysis.economics.break_even_price_inr_per_quintal === 2000, `Expected break-even price ₹2,000/qtl, got ${customAnalysis.economics.break_even_price_inr_per_quintal}`);
  // Break-even yield = ₹60,000 / (₹3,000 / 100 kg) = 2000 kg/ha
  assert(customAnalysis.economics.break_even_yield_kg_per_hectare === 2000, `Expected break-even yield 2,000 kg/ha, got ${customAnalysis.economics.break_even_yield_kg_per_hectare}`);
  console.log('✓ Economic formulas and break-even targets passed.\n');

  // Test 4: Soil Diagnostic & Lime Recommendation
  console.log('Test 4: Farmer Soil Test Diagnostic');
  const acidicSoil = evaluateFarmerSoilTest(4.8, 220, 35, 100, 0.6, 0.2);
  assert(acidicSoil.lime_recommendation_kg_per_ha > 0, 'Acidic soil (pH 4.8) should trigger lime recommendation');
  assert(acidicSoil.n_rating === 'Low', 'Available N of 220 kg/ha should be rated Low');
  assert(acidicSoil.p_rating === 'High', 'Available P of 35 kg/ha should be rated High');
  assert(acidicSoil.k_rating === 'Low', 'Available K of 100 kg/ha should be rated Low');
  assert(acidicSoil.oc_rating === 'Low', 'Organic carbon of 0.6% should be rated Low');
  assert(acidicSoil.fertilizer_adjustment_advice.length >= 4, 'Should give comprehensive advice for multiple nutrient limitations');
  console.log('✓ Soil test diagnostic passed.\n');

  // Test 5: Multi-Crop Land Allocation
  console.log('Test 5: Multi-Crop Land Allocation Aggregation');
  const allocation = farmAnalysisService.calculateLandAllocation(
    10,
    'acres',
    'Palakkad',
    [
      { crop: 'Rice', percent: 60 },
      { crop: 'Banana', percent: 40 },
    ]
  );
  assert(allocation.allocations.length === 2, 'Should contain 2 allocated crops');
  assert(Math.abs(allocation.allocations[0].area_acres - 6.0) < 0.1, '60% of 10 acres should equal 6 acres');
  assert(Math.abs(allocation.allocations[1].area_acres - 4.0) < 0.1, '40% of 10 acres should equal 4 acres');
  assert(allocation.aggregate_revenue_inr > 0, 'Aggregate revenue should be positive');
  assert(allocation.aggregate_cost_inr > 0, 'Aggregate cost should be positive');
  console.log('✓ Land allocation aggregation passed.\n');

  // Test 6: Kerala Base Price (Thara Vila) Floor
  console.log('Test 6: Kerala Statutory Base Price Verification');
  assert(KERALA_BASE_PRICES['Rice'].base_price_inr_per_kg === 28.20, 'Rice base price should be ₹28.20/kg');
  assert(KERALA_BASE_PRICES['Banana'].base_price_inr_per_kg === 30.00, 'Banana base price should be ₹30.00/kg');
  assert(KERALA_BASE_PRICES['Rubber'].base_price_inr_per_kg === 180.00, 'Rubber RPIS floor should be ₹180.00/kg');
  console.log('✓ Statutory base prices verified.\n');

  // Test 7: Weather Anomaly Quarantine Verification
  console.log('Test 7: Quarantined Weather Discrepancies Verification');
  const anomalyFile = path.resolve('data/metadata/weather_validation_anomalies_20260101_20261020_20261025182620.csv');
  assert(fs.existsSync(anomalyFile), 'Weather anomaly quarantine file must exist in data/metadata');
  const content = fs.readFileSync(anomalyFile, 'utf-8');
  const rows = content.trim().split('\n');
  assert(rows.length === 26, `Expected 25 quarantined records + 1 header, found ${rows.length}`);
  console.log('✓ 25 anomalous NASA POWER records correctly preserved in quarantine.\n');

  console.log('All 7 test suites executed successfully!');
}

runTests();
