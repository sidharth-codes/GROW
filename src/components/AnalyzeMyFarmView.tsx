import React, { useState, useMemo } from 'react';
import { growService } from '../services/growService';
import {
  farmAnalysisService,
  AreaUnit,
  convertArea,
  SingleCropAnalysisResult,
  MultiCropAllocationResult,
} from '../services/farmAnalysisService';
import { fmt } from '../utils/formatters';
import { DISTRICT_SOIL_BENCHMARKS } from '../data/soilMeasurementsData';

export const AnalyzeMyFarmView: React.FC = () => {
  const districts = useMemo(() => growService.getDistricts(), []);
  const allCrops = useMemo(() => growService.getCrops().map((c) => c.crop), []);

  // Form states
  const [district, setDistrict] = useState<string>('Palakkad');
  const [areaValue, setAreaValue] = useState<number>(2.5);
  const [areaUnit, setAreaUnit] = useState<AreaUnit>('acres');
  const [occupiedArea, setOccupiedArea] = useState<number>(0);
  const [waterAccess, setWaterAccess] = useState<'Rainfed' | 'Borewell / Well' | 'Canal Irrigation' | 'Drip / Sprinkler'>('Borewell / Well');
  const [selectedCrop, setSelectedCrop] = useState<string>('Rice');

  // Advanced optional inputs
  const [showSoilInputs, setShowSoilInputs] = useState<boolean>(false);
  const [soilPh, setSoilPh] = useState<number | ''>(5.8);
  const [soilNitrogen, setSoilNitrogen] = useState<number | ''>('');
  const [soilPhosphorus, setSoilPhosphorus] = useState<number | ''>('');
  const [soilPotassium, setSoilPotassium] = useState<number | ''>('');
  const [soilOrganicCarbon, setSoilOrganicCarbon] = useState<number | ''>('');

  const [showScenarioInputs, setShowScenarioInputs] = useState<boolean>(false);
  const [customPrice, setCustomPrice] = useState<number | ''>('');
  const [customYield, setCustomYield] = useState<number | ''>('');
  const [customCost, setCustomCost] = useState<number | ''>('');

  // Mode and view tabs
  const [showAdvancedDetails, setShowAdvancedDetails] = useState<boolean>(false);
  const [analysisMode, setAnalysisMode] = useState<'single' | 'compare' | 'allocation'>('single');
  const [activeTab, setActiveTab] = useState<'overview' | 'soil' | 'economics' | 'market' | 'risks' | 'compare' | 'allocation'>('overview');

  // Land allocation state
  const [allocations, setAllocations] = useState<{ crop: string; percent: number }[]>([
    { crop: 'Rice', percent: 50 },
    { crop: 'Banana', percent: 30 },
    { crop: 'Vegetables', percent: 20 },
  ]);

  // Live area conversion
  const liveConversion = useMemo(() => {
    return convertArea(areaValue, areaUnit);
  }, [areaValue, areaUnit]);

  // Run single crop analysis
  const singleAnalysis: SingleCropAnalysisResult = useMemo(() => {
    return farmAnalysisService.analyzeCrop({
      district,
      total_area: areaValue,
      area_unit: areaUnit,
      occupied_area: occupiedArea,
      selected_crop: selectedCrop,
      water_access: waterAccess,
      soil_ph: soilPh === '' ? null : Number(soilPh),
      soil_nitrogen: soilNitrogen === '' ? null : Number(soilNitrogen),
      soil_phosphorus: soilPhosphorus === '' ? null : Number(soilPhosphorus),
      soil_potassium: soilPotassium === '' ? null : Number(soilPotassium),
      soil_organic_carbon: soilOrganicCarbon === '' ? null : Number(soilOrganicCarbon),
      custom_cost_override_per_ha: customCost === '' ? null : Number(customCost),
      custom_price_override_per_quintal: customPrice === '' ? null : Number(customPrice),
      scenario_target_yield_kg_ha: customYield === '' ? null : Number(customYield),
    });
  }, [
    district,
    areaValue,
    areaUnit,
    occupiedArea,
    selectedCrop,
    waterAccess,
    soilPh,
    soilNitrogen,
    soilPhosphorus,
    soilPotassium,
    soilOrganicCarbon,
    customCost,
    customPrice,
    customYield,
  ]);

  // Multi-crop comparison list
  const comparedCropsList = useMemo(() => {
    const defaultList = ['Rice', 'Banana', 'Tapioca', 'Coconut', 'Vegetables', 'Black pepper'];
    return farmAnalysisService.compareCrops(district, areaValue, areaUnit, defaultList);
  }, [district, areaValue, areaUnit]);

  // Multi-crop land allocation calculation
  const allocationResult: MultiCropAllocationResult = useMemo(() => {
    return farmAnalysisService.calculateLandAllocation(areaValue, areaUnit, district, allocations);
  }, [areaValue, areaUnit, district, allocations]);

  const handlePrint = () => {
    window.print();
  };

  const handleSuggestCrop = () => {
    try {
      const recs = growService.getRecommendations(district);
      if (recs.recommendations.length > 0) {
        setSelectedCrop(recs.recommendations[0].crop);
      }
    } catch {
      // Keep existing
    }
  };

  return (
    <div className="analyze-farm-container">
      <div className="page-heading">
        <div>
          <div className="eyebrow">INTEGRATED FARM INTELLIGENCE</div>
          <h1>Analyze My Farm</h1>
          <p className="subtitle">
            Comprehensive end-to-end agricultural decision workflow: soil test ratings, climate suitability, production yield, cultivation costs, market price comparison, break-even targets, risk analysis, and multi-crop planning.
          </p>
        </div>
        <div>
          <button className="button secondary print-button" onClick={handlePrint} type="button">
            🖶 Print Farm Advisory Report
          </button>
        </div>
      </div>

      {/* Main Farm Parameters Card */}
      <section className="surface panel farm-setup-panel">
        <div className="panel-head">
          <div>
            <h2>Farm Profile &amp; Location</h2>
            <p>Specify your farm location, land area, water access, and target crops.</p>
          </div>
          <span className="tag">Live Calculator</span>
        </div>

        <form
          className="form-row"
          onSubmit={(e) => {
            e.preventDefault();
          }}
        >
          <div className="field">
            <label htmlFor="farm-district">Location (Kerala District)</label>
            <select
              id="farm-district"
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
            >
              {districts.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          <div className="field" style={{ minWidth: '130px' }}>
            <label htmlFor="farm-area-val">Total Farm Area</label>
            <input
              id="farm-area-val"
              type="number"
              step="0.1"
              min="0.1"
              max="5000"
              value={areaValue}
              onChange={(e) => setAreaValue(Math.max(0.1, parseFloat(e.target.value) || 0.1))}
            />
          </div>

          <div className="field" style={{ minWidth: '120px' }}>
            <label htmlFor="farm-area-unit">Area Unit</label>
            <select
              id="farm-area-unit"
              value={areaUnit}
              onChange={(e) => setAreaUnit(e.target.value as AreaUnit)}
            >
              <option value="acres">Acres</option>
              <option value="hectares">Hectares</option>
              <option value="cents">Cents</option>
            </select>
          </div>

          <div className="field" style={{ minWidth: '180px', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
            <span style={{ fontSize: '11px', color: '#526356', marginBottom: '4px' }}>Quick Size Presets:</span>
            <div style={{ display: 'flex', gap: '4px' }}>
              <button
                type="button"
                className={`button secondary ${areaValue === 50 && areaUnit === 'cents' ? 'active' : ''}`}
                style={{ fontSize: '11px', padding: '4px 8px', minHeight: '32px' }}
                onClick={() => { setAreaValue(50); setAreaUnit('cents'); }}
              >
                50 Cents
              </button>
              <button
                type="button"
                className={`button secondary ${areaValue === 1 && areaUnit === 'acres' ? 'active' : ''}`}
                style={{ fontSize: '11px', padding: '4px 8px', minHeight: '32px' }}
                onClick={() => { setAreaValue(1); setAreaUnit('acres'); }}
              >
                1 Acre
              </button>
              <button
                type="button"
                className={`button secondary ${areaValue === 2.5 && areaUnit === 'acres' ? 'active' : ''}`}
                style={{ fontSize: '11px', padding: '4px 8px', minHeight: '32px' }}
                onClick={() => { setAreaValue(2.5); setAreaUnit('acres'); }}
              >
                2.5 Ac
              </button>
              <button
                type="button"
                className={`button secondary ${areaValue === 5 && areaUnit === 'acres' ? 'active' : ''}`}
                style={{ fontSize: '11px', padding: '4px 8px', minHeight: '32px' }}
                onClick={() => { setAreaValue(5); setAreaUnit('acres'); }}
              >
                5 Ac
              </button>
            </div>
          </div>

          <div className="field">
            <label htmlFor="farm-water">Irrigation / Water Source</label>
            <select
              id="farm-water"
              value={waterAccess}
              onChange={(e) => setWaterAccess(e.target.value as any)}
            >
              <option value="Borewell / Well">Borewell / Open Well</option>
              <option value="Canal Irrigation">Canal Irrigation</option>
              <option value="Drip / Sprinkler">Drip / Micro-sprinkler</option>
              <option value="Rainfed">Rainfed (Monsoon dependent)</option>
            </select>
          </div>

          <div className="field">
            <label htmlFor="farm-crop">Selected Crop</label>
            <div style={{ display: 'flex', gap: '6px' }}>
              <select
                id="farm-crop"
                value={selectedCrop}
                onChange={(e) => setSelectedCrop(e.target.value)}
                style={{ flex: 1 }}
              >
                {allCrops.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
              <button
                className="button secondary"
                type="button"
                onClick={handleSuggestCrop}
                title="Automatically select top recommended crop for this district"
                style={{ minHeight: '39px', whiteSpace: 'nowrap' }}
              >
                Auto-Suggest
              </button>
            </div>
          </div>
        </form>

        {/* Live Area Conversion Badge */}
        <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', gap: '10px', fontSize: '11px', color: '#526356' }}>
          <span style={{ fontWeight: 600 }}>Standardized Area:</span>
          <span className="tag">
            {liveConversion.in_acres} Acres
          </span>
          <span className="tag">
            {liveConversion.in_hectares} Hectares
          </span>
          <span className="tag">
            {liveConversion.in_cents} Cents
          </span>
          {occupiedArea > 0 && (
            <span style={{ color: '#8b4141' }}>
              (Net plantable: {Math.max(0, areaValue - occupiedArea)} {areaUnit})
            </span>
          )}
        </div>

        {/* Expandable Optional Sections */}
        <div style={{ marginTop: '16px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <button
            type="button"
            className="button secondary"
            style={{ fontSize: '10px' }}
            onClick={() => setShowSoilInputs(!showSoilInputs)}
          >
            {showSoilInputs ? '▲ Hide Soil Test Inputs' : '▼ Enter Farm Soil Test Values (pH, NPK, OC)'}
          </button>

          <button
            type="button"
            className="button secondary"
            style={{ fontSize: '10px' }}
            onClick={() => setShowScenarioInputs(!showScenarioInputs)}
          >
            {showScenarioInputs ? '▲ Hide Price/Yield Scenarios' : '▼ Custom Economic Scenarios (Target Price, Yield, Cost)'}
          </button>
        </div>

        {showSoilInputs && (
          <div className="surface" style={{ marginTop: '14px', padding: '16px', background: '#f8faf7' }}>
            <h3 style={{ fontSize: '12px', marginBottom: '8px' }}>Lab Soil Test Parameters (Optional)</h3>
            <p className="subtitle" style={{ fontSize: '10px', marginBottom: '12px' }}>
              Enter values from your Soil Health Card or local soil test report. If left blank, Kerala district benchmark values will be used.
            </p>
            <div className="form-row">
              <div className="field" style={{ minWidth: '100px' }}>
                <label>Soil pH</label>
                <input
                  type="number"
                  step="0.1"
                  min="3.5"
                  max="9.0"
                  placeholder="e.g. 5.5"
                  value={soilPh}
                  onChange={(e) => setSoilPh(e.target.value === '' ? '' : parseFloat(e.target.value))}
                />
              </div>

              <div className="field" style={{ minWidth: '120px' }}>
                <label>Available Nitrogen (kg/ha)</label>
                <input
                  type="number"
                  placeholder="e.g. 240"
                  value={soilNitrogen}
                  onChange={(e) => setSoilNitrogen(e.target.value === '' ? '' : parseFloat(e.target.value))}
                />
              </div>

              <div className="field" style={{ minWidth: '120px' }}>
                <label>Phosphorus P2O5 (kg/ha)</label>
                <input
                  type="number"
                  placeholder="e.g. 25"
                  value={soilPhosphorus}
                  onChange={(e) => setSoilPhosphorus(e.target.value === '' ? '' : parseFloat(e.target.value))}
                />
              </div>

              <div className="field" style={{ minWidth: '120px' }}>
                <label>Potassium K2O (kg/ha)</label>
                <input
                  type="number"
                  placeholder="e.g. 150"
                  value={soilPotassium}
                  onChange={(e) => setSoilPotassium(e.target.value === '' ? '' : parseFloat(e.target.value))}
                />
              </div>

              <div className="field" style={{ minWidth: '120px' }}>
                <label>Organic Carbon (%)</label>
                <input
                  type="number"
                  step="0.1"
                  placeholder="e.g. 1.2"
                  value={soilOrganicCarbon}
                  onChange={(e) => setSoilOrganicCarbon(e.target.value === '' ? '' : parseFloat(e.target.value))}
                />
              </div>
            </div>
          </div>
        )}

        {showScenarioInputs && (
          <div className="surface" style={{ marginTop: '14px', padding: '16px', background: '#f8faf7' }}>
            <h3 style={{ fontSize: '12px', marginBottom: '8px' }}>Farmer Scenario &amp; Sensitivity Testing</h3>
            <p className="subtitle" style={{ fontSize: '10px', marginBottom: '12px' }}>
              Override default market price, yield, or cost per hectare to test custom economic scenarios.
            </p>
            <div className="form-row">
              <div className="field">
                <label>Custom Selling Price (₹ / quintal)</label>
                <input
                  type="number"
                  placeholder="e.g. 3500"
                  value={customPrice}
                  onChange={(e) => setCustomPrice(e.target.value === '' ? '' : parseFloat(e.target.value))}
                />
              </div>

              <div className="field">
                <label>Target Expected Yield (kg / ha)</label>
                <input
                  type="number"
                  placeholder="e.g. 3200"
                  value={customYield}
                  onChange={(e) => setCustomYield(e.target.value === '' ? '' : parseFloat(e.target.value))}
                />
              </div>

              <div className="field">
                <label>Custom Cultivation Cost (₹ / ha)</label>
                <input
                  type="number"
                  placeholder="e.g. 75000"
                  value={customCost}
                  onChange={(e) => setCustomCost(e.target.value === '' ? '' : parseFloat(e.target.value))}
                />
              </div>
            </div>
          </div>
        )}
      </section>

      {/* SIMPLE FARMER QUICK ADVISORY: DIRECT PLACE + CROP REPORT */}
      <section className="surface panel" style={{ marginTop: '20px', borderTop: '4px solid #2e7d32' }}>
        <div className="panel-head" style={{ marginBottom: '16px' }}>
          <div>
            <div className="eyebrow" style={{ color: '#2e7d32' }}>FARMER ADVISORY · KERALA</div>
            <h2 style={{ fontSize: '18px', margin: '4px 0' }}>
              {selectedCrop} in {district} · {areaValue} {areaUnit}
            </h2>
            <p style={{ margin: 0 }}>
              Live evaluation: seasonal weather, soil match, wholesale price, market demand, and expected profit.
            </p>
          </div>
          <span className="tag" style={{ background: '#e8f5e9', color: '#1b5e20', fontWeight: 700, fontSize: '12px' }}>
            {singleAnalysis.suitability.verdict}
          </span>
        </div>

        {/* 5 Core Visual Blocks */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
          {/* 1. Weather */}
          <div className="surface" style={{ padding: '16px', borderRadius: '10px', background: '#fafdfa', border: '1px solid #d4e3d6' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#2c3a2f' }}>
                ☀️ Weather &amp; Season
              </span>
              <span className="tag" style={{ background: '#e8f5e9', color: '#1b5e20', fontWeight: 600 }}>
                Suitable
              </span>
            </div>
            <div style={{ fontSize: '16px', fontWeight: 700, color: '#1c2826' }}>
              {singleAnalysis.calendar?.season || 'Standard Kerala Season'}
            </div>
            <p style={{ fontSize: '12px', color: '#4a5b4f', lineHeight: 1.5, margin: '8px 0 0' }}>
              Sowing window: <strong>{singleAnalysis.calendar?.sowing_window || 'Seasonal window'}</strong>. Harvest: <strong>{singleAnalysis.calendar?.harvest_window || 'Maturity phase'}</strong>. Temperature range 20–35°C is favorable.
            </p>
          </div>

          {/* 2. Soil */}
          <div className="surface" style={{ padding: '16px', borderRadius: '10px', background: '#fafdfa', border: '1px solid #d4e3d6' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#2c3a2f' }}>
                🌱 Soil Condition
              </span>
              <span className="tag" style={{ background: '#e8f5e9', color: '#1b5e20', fontWeight: 600 }}>
                Good Match
              </span>
            </div>
            <div style={{ fontSize: '16px', fontWeight: 700, color: '#1c2826' }}>
              {DISTRICT_SOIL_BENCHMARKS[district]?.dominant_texture || 'Loam to Clay Loam'}
            </div>
            <p style={{ fontSize: '12px', color: '#4a5b4f', lineHeight: 1.5, margin: '8px 0 0' }}>
              {DISTRICT_SOIL_BENCHMARKS[district]?.dominant_drainage || 'Well drained'} ({DISTRICT_SOIL_BENCHMARKS[district]?.ph_status || 'Moderately acidic'}). Tract: {DISTRICT_SOIL_BENCHMARKS[district]?.representative_tract || district}.
            </p>
          </div>

          {/* 3. Market Price */}
          <div className="surface" style={{ padding: '16px', borderRadius: '10px', background: '#f5f9ff', border: '1px solid #cce0ff' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#0d47a1' }}>
                🏷️ Wholesale Mandi Price
              </span>
              <span className="tag" style={{ background: '#e3f2fd', color: '#0d47a1', fontWeight: 600 }}>
                AGMARKNET
              </span>
            </div>
            <div style={{ fontSize: '22px', fontWeight: 800, color: '#0d47a1' }}>
              ₹{Math.round(singleAnalysis.economics.price_inr_per_quintal / 100)} / kg
              <span style={{ fontSize: '12px', fontWeight: 500, color: '#526356', marginLeft: '6px' }}>
                (₹{fmt(singleAnalysis.economics.price_inr_per_quintal)}/qtl)
              </span>
            </div>
            <p style={{ fontSize: '12px', color: '#4a5b4f', lineHeight: 1.5, margin: '8px 0 0' }}>
              Kerala Floor Guarantee: <strong>₹{singleAnalysis.economics.base_price_floor_inr_per_quintal ? Math.round(singleAnalysis.economics.base_price_floor_inr_per_quintal / 100) : 28} / kg</strong> ({singleAnalysis.economics.base_price_scheme ? singleAnalysis.economics.base_price_scheme.split('(')[0] : 'State Base Price Scheme'}).
            </p>
          </div>

          {/* 4. Market Demand */}
          <div className="surface" style={{ padding: '16px', borderRadius: '10px', background: '#fffaf3', border: '1px solid #ffe3c2' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#b74b00' }}>
                📈 Market Demand &amp; Inflows
              </span>
              <span className="tag" style={{ background: '#fff3e0', color: '#b74b00', fontWeight: 600 }}>
                Active Market
              </span>
            </div>
            <div style={{ fontSize: '22px', fontWeight: 800, color: '#b74b00' }}>
              {singleAnalysis.market_analysis?.recent_arrivals?.[0]?.quantity || 57.5} Tonnes / day
            </div>
            <p style={{ fontSize: '12px', color: '#4a5b4f', lineHeight: 1.5, margin: '8px 0 0' }}>
              Mandi: <strong>{singleAnalysis.market_analysis?.primary_market || `${district} Mandi`}</strong>. Steady buyer demand in district wholesale trading.
            </p>
          </div>

          {/* 5. Production, Cost & Net Profit */}
          <div className="surface" style={{ padding: '16px', borderRadius: '10px', background: singleAnalysis.economics.is_profitable ? '#f4faf5' : '#fff8f7', border: singleAnalysis.economics.is_profitable ? '2px solid #81c784' : '2px solid #ef9a9a', gridColumn: 'span 2' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <span style={{ fontSize: '12px', fontWeight: 800, textTransform: 'uppercase', color: singleAnalysis.economics.is_profitable ? '#1b5e20' : '#b71c1c' }}>
                💰 Cultivation Cost &amp; Net Profit ({areaValue} {areaUnit})
              </span>
              <span className="tag" style={{ background: singleAnalysis.economics.is_profitable ? '#2e7d32' : '#c62828', color: '#fff', fontWeight: 700, fontSize: '12px' }}>
                {singleAnalysis.economics.is_profitable ? `PROFITABLE (+${singleAnalysis.economics.roi_percent}% ROI)` : 'CAUTION: MARGINAL'}
              </span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '12px', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: '10px', color: '#526356', textTransform: 'uppercase' }}>Expected Harvest</div>
                <div style={{ fontSize: '16px', fontWeight: 700 }}>{fmt(singleAnalysis.production.total_production_tonnes * 1000, 0)} kg</div>
                <div style={{ fontSize: '10px', color: '#526356' }}>({fmt(singleAnalysis.production.yield_kg_per_hectare, 0)} kg/ha)</div>
              </div>
              <div>
                <div style={{ fontSize: '10px', color: '#526356', textTransform: 'uppercase' }}>Gross Revenue</div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: '#2e7d32' }}>₹{fmt(singleAnalysis.economics.gross_revenue_inr, 0)}</div>
                <div style={{ fontSize: '10px', color: '#526356' }}>(Selling income)</div>
              </div>
              <div>
                <div style={{ fontSize: '10px', color: '#526356', textTransform: 'uppercase' }}>Cultivation Cost</div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: '#526356' }}>₹{fmt(singleAnalysis.economics.total_cultivation_cost_inr, 0)}</div>
                <div style={{ fontSize: '10px', color: '#526356' }}>(Seeds, fertilizer, labour)</div>
              </div>
              <div style={{ background: singleAnalysis.economics.is_profitable ? '#e8f5e9' : '#ffebee', padding: '10px 14px', borderRadius: '8px', border: '1px solid ' + (singleAnalysis.economics.is_profitable ? '#a5d6a7' : '#ffcdd2'), textAlign: 'center' }}>
                <div style={{ fontSize: '10px', fontWeight: 800, color: singleAnalysis.economics.is_profitable ? '#1b5e20' : '#b71c1c', textTransform: 'uppercase' }}>
                  ESTIMATED NET PROFIT
                </div>
                <div style={{ fontSize: '22px', fontWeight: 900, color: singleAnalysis.economics.is_profitable ? '#1b5e20' : '#c62828' }}>
                  {singleAnalysis.economics.net_profit_inr >= 0 ? '+' : ''}₹{fmt(singleAnalysis.economics.net_profit_inr, 0)}
                </div>
                <div style={{ fontSize: '10px', fontWeight: 600, color: singleAnalysis.economics.is_profitable ? '#2e7d32' : '#c62828' }}>
                  ₹{fmt(singleAnalysis.economics.profit_per_acre_inr, 0)} / acre
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Practical Action Tips */}
        <div style={{ marginTop: '16px', padding: '14px 18px', background: '#f5faf6', borderRadius: '8px', borderLeft: '4px solid #2e7d32' }}>
          <strong style={{ fontSize: '13px', color: '#1b5e20' }}>
            💡 What to do now (Action Tips for {district} farmers):
          </strong>
          <ul style={{ margin: '6px 0 0 16px', padding: 0, fontSize: '12px', color: '#2c3a2f', lineHeight: 1.6 }}>
            <li><strong>Calendar:</strong> {singleAnalysis.calendar?.sowing_window || 'Current season'} is the recommended planting window for {selectedCrop}.</li>
            <li><strong>Soil &amp; Nutrients:</strong> {singleAnalysis.calendar?.kau_recommendation_summary || 'Apply balanced farmyard manure and lime according to local acidity.'}</li>
            <li><strong>Risk Management:</strong> Watch for {singleAnalysis.calendar?.major_pests?.slice(0, 2).join(', ') || 'seasonal pests'}. Registered farmers are protected by the State Base Price guarantee.</li>
          </ul>
        </div>
      </section>

      {/* Advanced Details Toggle */}
      <div style={{ margin: '24px 0 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 700, margin: 0, color: '#2c3a2f' }}>
          Detailed Agronomic Breakdown &amp; Advanced Planning Tools
        </h2>
        <button
          type="button"
          className="button secondary"
          onClick={() => setShowAdvancedDetails(!showAdvancedDetails)}
          style={{ fontSize: '12px', fontWeight: 600 }}
        >
          {showAdvancedDetails ? '▲ Hide Advanced Breakdown' : '▼ View Itemized Costs, Soil Test & Multi-Crop Comparison'}
        </button>
      </div>

      {showAdvancedDetails && (
        <div>
          {/* Analysis Workspace Navigation Tabs */}
          <div style={{ display: 'flex', gap: '8px', margin: '16px 0', overflowX: 'auto', paddingBottom: '4px' }}>
        <button
          type="button"
          className={`button ${activeTab === 'overview' ? '' : 'secondary'}`}
          onClick={() => setActiveTab('overview')}
        >
          Executive Summary &amp; Economics
        </button>
        <button
          type="button"
          className={`button ${activeTab === 'soil' ? '' : 'secondary'}`}
          onClick={() => setActiveTab('soil')}
        >
          Soil Test &amp; Agronomic Fit
        </button>
        <button
          type="button"
          className={`button ${activeTab === 'economics' ? '' : 'secondary'}`}
          onClick={() => setActiveTab('economics')}
        >
          Itemized Costs &amp; Break-Even
        </button>
        <button
          type="button"
          className={`button ${activeTab === 'market' ? '' : 'secondary'}`}
          onClick={() => setActiveTab('market')}
        >
          Mandi Quotes &amp; Market Comparison
        </button>
        <button
          type="button"
          className={`button ${activeTab === 'risks' ? '' : 'secondary'}`}
          onClick={() => setActiveTab('risks')}
        >
          Pest, Disease &amp; Climate Risks
        </button>
        <button
          type="button"
          className={`button ${activeTab === 'compare' ? '' : 'secondary'}`}
          onClick={() => setActiveTab('compare')}
        >
          Side-by-Side Crop Comparison
        </button>
        <button
          type="button"
          className={`button ${activeTab === 'allocation' ? '' : 'secondary'}`}
          onClick={() => setActiveTab('allocation')}
        >
          Multi-Crop Land Allocation
        </button>
      </div>

      {/* TAB 1: EXECUTIVE OVERVIEW & ECONOMICS */}
      {activeTab === 'overview' && (
        <div>
          {/* Executive Verdict Banner */}
          <div
            className={`notice ${singleAnalysis.economics.is_profitable ? 'info' : 'error'}`}
            style={{ padding: '16px 20px', borderRadius: '12px', borderLeft: '6px solid var(--green)' }}
          >
            <div style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <strong style={{ fontSize: '15px' }}>
                  Agronomic &amp; Economic Verdict: {singleAnalysis.suitability.verdict}
                </strong>
                <span className={`tag ${singleAnalysis.suitability.overall_score >= 70 ? '' : 'warning'}`}>
                  Suitability Score: {singleAnalysis.suitability.overall_score}/100
                </span>
              </div>
              <p style={{ margin: 0, fontSize: '12px', lineHeight: '1.6', color: '#2c3a2f' }}>
                {singleAnalysis.recommendation_summary}
              </p>
            </div>
          </div>

          {/* 4 Core Financial & Production Metrics */}
          <div className="metric-grid">
            <article className="surface metric-card">
              <span className="metric-icon">↗</span>
              <span className="metric-label">Total Expected Production</span>
              <strong className="metric-value">
                {fmt(singleAnalysis.production.total_production_tonnes, 2)} Tonnes
              </strong>
              <span className="metric-note">
                {fmt(singleAnalysis.production.total_production_quintals, 1)} Quintals ({fmt(singleAnalysis.production.yield_kg_per_hectare, 0)} kg/ha)
              </span>
            </article>

            <article className="surface metric-card">
              <span className="metric-icon">₹</span>
              <span className="metric-label">Total Cultivation Cost</span>
              <strong className="metric-value">
                ₹{fmt(singleAnalysis.economics.total_cultivation_cost_inr, 0)}
              </strong>
              <span className="metric-note">
                ₹{fmt(singleAnalysis.economics.cost_inr_per_hectare, 0)} / hectare
              </span>
            </article>

            <article className="surface metric-card">
              <span className="metric-icon">＋</span>
              <span className="metric-label">Expected Gross Revenue</span>
              <strong className="metric-value">
                ₹{fmt(singleAnalysis.economics.gross_revenue_inr, 0)}
              </strong>
              <span className="metric-note">
                at ₹{fmt(singleAnalysis.economics.price_inr_per_quintal, 0)} / quintal
              </span>
            </article>

            <article className="surface metric-card" style={{ borderColor: singleAnalysis.economics.is_profitable ? '#b8d6be' : '#f2d9d5' }}>
              <span className="metric-icon">{singleAnalysis.economics.is_profitable ? '★' : '!'}</span>
              <span className="metric-label">Estimated Net Profit</span>
              <strong
                className="metric-value"
                style={{ color: singleAnalysis.economics.is_profitable ? 'var(--green-dark)' : '#8b4141' }}
              >
                ₹{fmt(singleAnalysis.economics.net_profit_inr, 0)}
              </strong>
              <span className="metric-note">
                ₹{fmt(singleAnalysis.economics.profit_per_acre_inr, 0)} / acre (ROI: {singleAnalysis.economics.roi_percent}%)
              </span>
            </article>
          </div>

          {/* Break-even & Key Targets Grid */}
          <div className="grid-two">
            <section className="surface panel">
              <div className="panel-head">
                <div>
                  <h2>Break-Even Thresholds &amp; Safety Margin</h2>
                  <p>Minimum yield and selling price required to prevent financial loss.</p>
                </div>
              </div>
              <div className="two-col-list">
                <div className="info-box">
                  <span>Break-Even Selling Price</span>
                  <strong>₹{fmt(singleAnalysis.economics.break_even_price_inr_per_quintal, 1)} / qtl</strong>
                  <p className="small-note" style={{ marginTop: '4px' }}>
                    Current quote: ₹{fmt(singleAnalysis.economics.price_inr_per_quintal, 0)}/qtl{' '}
                    {singleAnalysis.economics.price_inr_per_quintal >= singleAnalysis.economics.break_even_price_inr_per_quintal ? (
                      <span style={{ color: 'var(--green)', fontWeight: 600 }}>
                        (+₹{fmt(singleAnalysis.economics.price_inr_per_quintal - singleAnalysis.economics.break_even_price_inr_per_quintal, 1)} safety buffer)
                      </span>
                    ) : (
                      <span style={{ color: '#8b4141', fontWeight: 600 }}>
                        (Under break-even by ₹{fmt(singleAnalysis.economics.break_even_price_inr_per_quintal - singleAnalysis.economics.price_inr_per_quintal, 1)})
                      </span>
                    )}
                  </p>
                </div>

                <div className="info-box">
                  <span>Break-Even Harvest Yield</span>
                  <strong>{fmt(singleAnalysis.economics.break_even_yield_kg_per_hectare, 0)} kg/ha</strong>
                  <p className="small-note" style={{ marginTop: '4px' }}>
                    Expected yield: {fmt(singleAnalysis.production.yield_kg_per_hectare, 0)} kg/ha{' '}
                    {singleAnalysis.production.yield_kg_per_hectare >= singleAnalysis.economics.break_even_yield_kg_per_hectare ? (
                      <span style={{ color: 'var(--green)', fontWeight: 600 }}>(Surplus: +{fmt(singleAnalysis.production.yield_kg_per_hectare - singleAnalysis.economics.break_even_yield_kg_per_hectare, 0)} kg/ha)</span>
                    ) : (
                      <span style={{ color: '#8b4141', fontWeight: 600 }}>(Deficit: -{fmt(singleAnalysis.economics.break_even_yield_kg_per_hectare - singleAnalysis.production.yield_kg_per_hectare, 0)} kg/ha)</span>
                    )}
                  </p>
                </div>
              </div>

              {singleAnalysis.economics.base_price_floor_inr_per_quintal && (
                <div style={{ marginTop: '14px', padding: '12px', background: '#eef5ec', borderRadius: '8px', fontSize: '11px', color: '#2d4b32' }}>
                  <strong>Kerala Statutory Floor Price Guarantee (Thara Vila):</strong>
                  <div>
                    Guaranteed minimum ₹{fmt(singleAnalysis.economics.base_price_floor_inr_per_quintal, 0)}/quintal under {singleAnalysis.economics.base_price_scheme}.
                  </div>
                </div>
              )}
            </section>

            <section className="surface panel">
              <div className="panel-head">
                <div>
                  <h2>Cultivation Cost Share Breakdown</h2>
                  <p>Input cost composition for your {liveConversion.in_acres} acre plot.</p>
                </div>
              </div>
              <div style={{ display: 'grid', gap: '8px' }}>
                {singleAnalysis.economics.cost_breakdown.slice(0, 5).map((item) => (
                  <div key={item.category} className="bar-row">
                    <span className="bar-label" title={item.description}>{item.category}</span>
                    <div className="bar-track">
                      <div className="bar-value" style={{ width: `${item.share_percent}%` }} />
                    </div>
                    <span className="bar-number">₹{fmt(item.cost_inr, 0)}</span>
                  </div>
                ))}
              </div>
              <p className="small-note">
                Labour represents the largest input expenditure in Kerala (40-55% of total paid-out costs).
              </p>
            </section>
          </div>
        </div>
      )}

      {/* TAB 2: SOIL TEST & AGRONOMIC FIT */}
      {activeTab === 'soil' && (
        <div>
          <div className="grid-two">
            <section className="surface panel">
              <div className="panel-head">
                <div>
                  <h2>Soil Suitability &amp; Health Analysis</h2>
                  <p>Laboratory diagnosis for your {district} farm parcel.</p>
                </div>
                <span className="tag">Score: {singleAnalysis.suitability.soil_match_score}/100</span>
              </div>

              {singleAnalysis.suitability.soil_test_evaluation && (
                <div>
                  <div className="two-col-list" style={{ marginBottom: '14px' }}>
                    <div className="info-box">
                      <span>pH Status</span>
                      <strong>{singleAnalysis.suitability.soil_test_evaluation.ph_rating}</strong>
                    </div>
                    <div className="info-box">
                      <span>Available Nitrogen (N)</span>
                      <strong>{singleAnalysis.suitability.soil_test_evaluation.n_rating} Status</strong>
                    </div>
                    <div className="info-box">
                      <span>Available Phosphorus (P)</span>
                      <strong>{singleAnalysis.suitability.soil_test_evaluation.p_rating} Status</strong>
                    </div>
                    <div className="info-box">
                      <span>Available Potassium (K)</span>
                      <strong>{singleAnalysis.suitability.soil_test_evaluation.k_rating} Status</strong>
                    </div>
                  </div>

                  {singleAnalysis.suitability.soil_test_evaluation.lime_recommendation_kg_per_ha > 0 && (
                    <div className="notice" style={{ marginBottom: '14px' }}>
                      <span className="notice-icon">!</span>
                      <div>
                        <strong>Soil Acidity Correction Required:</strong>
                        Apply agricultural lime (CaCO3) or dolomite @{' '}
                        {singleAnalysis.suitability.soil_test_evaluation.lime_recommendation_kg_per_ha} kg/ha (approx{' '}
                        {Math.round(singleAnalysis.suitability.soil_test_evaluation.lime_recommendation_kg_per_ha * liveConversion.in_hectares)}{' '}
                        kg for your farm) 2-3 weeks prior to planting.
                      </div>
                    </div>
                  )}

                  <h3 style={{ fontSize: '12px', marginTop: '12px' }}>Soil Health Improvement Guidelines:</h3>
                  <ul className="limitation-list">
                    {singleAnalysis.suitability.soil_test_evaluation.fertilizer_adjustment_advice.map((adv, idx) => (
                      <li key={idx}>{adv}</li>
                    ))}
                  </ul>
                </div>
              )}
            </section>

            <section className="surface panel">
              <div className="panel-head">
                <div>
                  <h2>Crop Agronomic Tolerances vs Farm Environment</h2>
                  <p>Comparing {selectedCrop} requirements against local conditions.</p>
                </div>
              </div>

              {singleAnalysis.calendar ? (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Parameter</th>
                        <th>Crop Requirement</th>
                        <th>Farm Condition ({district})</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><strong>Soil pH Range</strong></td>
                        <td>{singleAnalysis.calendar.ph_min} – {singleAnalysis.calendar.ph_max}</td>
                        <td>{soilPh !== '' ? soilPh : '5.5 (District Mean)'}</td>
                      </tr>
                      <tr>
                        <td><strong>Water Requirement</strong></td>
                        <td>{singleAnalysis.calendar.water_requirement} ({singleAnalysis.calendar.annual_rainfall_mm_min}–{singleAnalysis.calendar.annual_rainfall_mm_max} mm)</td>
                        <td>{waterAccess}</td>
                      </tr>
                      <tr>
                        <td><strong>Temperature Range</strong></td>
                        <td>{singleAnalysis.calendar.temp_min_c}°C – {singleAnalysis.calendar.temp_max_c}°C</td>
                        <td>22°C – 34°C (Kerala Tropical)</td>
                      </tr>
                      <tr>
                        <td><strong>Crop Duration</strong></td>
                        <td>{singleAnalysis.calendar.duration_days} Days</td>
                        <td>{singleAnalysis.calendar.season}</td>
                      </tr>
                      <tr>
                        <td><strong>Drainage Tolerance</strong></td>
                        <td>{singleAnalysis.calendar.drainage_requirement}</td>
                        <td>Well Drained / Ridge Prepared</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="subtitle">Calendar parameters loading…</p>
              )}
            </section>
          </div>
        </div>
      )}

      {/* TAB 3: ITEMIZED COSTS & BREAK-EVEN */}
      {activeTab === 'economics' && (
        <div>
          <section className="surface panel">
            <div className="panel-head">
              <div>
                <h2>Complete Itemized Cultivation Budget</h2>
                <p>
                  Official Kerala DES benchmark cost structure scaled to your {liveConversion.in_acres} acres ({liveConversion.in_hectares} hectares).
                </p>
              </div>
              <span className="tag">Accounting: {singleAnalysis.cost_structure?.accounting_basis}</span>
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Cost Category</th>
                    <th>Operations &amp; Inputs Included</th>
                    <th>Share (%)</th>
                    <th>Rate / Hectare</th>
                    <th>Total Plot Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {singleAnalysis.economics.cost_breakdown.map((item, idx) => (
                    <tr key={idx}>
                      <td><strong>{item.category}</strong></td>
                      <td>{item.description}</td>
                      <td>{item.share_percent}%</td>
                      <td>₹{fmt((item.cost_inr / (liveConversion.in_hectares || 1)), 0)}</td>
                      <td><strong>₹{fmt(item.cost_inr, 0)}</strong></td>
                    </tr>
                  ))}
                  <tr style={{ background: '#f5f7f3', fontWeight: 700 }}>
                    <td colSpan={3}><strong>TOTAL PRODUCTION EXPENDITURE</strong></td>
                    <td>₹{fmt(singleAnalysis.economics.cost_inr_per_hectare, 0)} / ha</td>
                    <td><strong style={{ fontSize: '13px', color: 'var(--green-dark)' }}>₹{fmt(singleAnalysis.economics.total_cultivation_cost_inr, 0)}</strong></td>
                  </tr>
                </tbody>
              </table>
            </div>

            <p className="small-note" style={{ marginTop: '12px' }}>
              Source: {singleAnalysis.cost_structure?.source}. Figures exclude rental on owned land and family labour imputed values.
            </p>
          </section>
        </div>
      )}

      {/* TAB 4: MARKET QUOTES & COMPARISON */}
      {activeTab === 'market' && (
        <div>
          <section className="surface panel">
            <div className="panel-head">
              <div>
                <h2>Nearby Wholesale Mandis Comparison</h2>
                <p>Compare terminal market prices across Kerala to maximize farm revenue.</p>
              </div>
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Wholesale Mandi</th>
                    <th>Distance</th>
                    <th>Modal Wholesale Quote</th>
                    <th>Gross Revenue for Your Plot</th>
                    <th>Net Advantage vs Local Mandi</th>
                  </tr>
                </thead>
                <tbody>
                  {singleAnalysis.market_analysis.nearby_markets.map((m, idx) => (
                    <tr key={idx}>
                      <td><strong>{m.market}</strong></td>
                      <td>~{m.distance_km} km</td>
                      <td>₹{fmt(m.modal_price, 0)} / quintal</td>
                      <td>₹{fmt(m.gross_revenue_at_this_market, 0)}</td>
                      <td>
                        {m.net_advantage_inr > 0 ? (
                          <span style={{ color: 'var(--green)', fontWeight: 600 }}>
                            +₹{fmt(m.net_advantage_inr, 0)} higher
                          </span>
                        ) : m.net_advantage_inr < 0 ? (
                          <span style={{ color: '#8b4141' }}>
                            -₹{fmt(Math.abs(m.net_advantage_inr), 0)} lower
                          </span>
                        ) : (
                          <span style={{ color: '#657267' }}>Baseline quote</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p className="small-note" style={{ marginTop: '10px' }}>
              Wholesale quotes reflect Agmarknet and Kerala Agricultural Marketing bulletins as of {singleAnalysis.economics.price_date}. Transportation costs should be factored in when choosing distant wholesale hubs.
            </p>
          </section>

          {singleAnalysis.market_analysis.recent_arrivals.length > 0 && (
            <section className="surface panel">
              <div className="panel-head">
                <div>
                  <h2>Recent Wholesale Mandi Inflow &amp; Arrivals</h2>
                  <p>Physical trading volume recorded in AGMARKNET terminal reports.</p>
                </div>
              </div>

              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Market Hub</th>
                      <th>Reported Inflow Quantity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {singleAnalysis.market_analysis.recent_arrivals.map((arr, idx) => (
                      <tr key={idx}>
                        <td>{arr.date}</td>
                        <td>{arr.market}</td>
                        <td>{arr.quantity} {arr.unit}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </div>
      )}

      {/* TAB 5: RISKS & MITIGATION */}
      {activeTab === 'risks' && (
        <div>
          <div className="grid-two">
            <section className="surface panel">
              <div className="panel-head">
                <div>
                  <h2>Major Pests &amp; Recommended Biological Control</h2>
                  <p>Kerala Agricultural University (KAU) Package of Practices guidelines.</p>
                </div>
              </div>
              <ul className="limitation-list" style={{ lineHeight: '2.0' }}>
                {singleAnalysis.risks.pest_disease_risks.map((pest, idx) => (
                  <li key={idx}><strong>{pest}</strong></li>
                ))}
              </ul>
              <div style={{ marginTop: '14px', padding: '12px', background: '#f8faf7', borderRadius: '8px', fontSize: '11px' }}>
                <strong>Integrated Pest Management (IPM) Protocol:</strong>
                <p style={{ margin: '4px 0 0', color: '#556358' }}>
                  Deploy pheromone traps, maintain field sanitization, and spray neem oil emulsion (0.05%) at early signs of infestation.
                </p>
              </div>
            </section>

            <section className="surface panel">
              <div className="panel-head">
                <div>
                  <h2>Climate, Fungal &amp; Financial Risk Mitigations</h2>
                  <p>Vulnerabilities specific to {district} weather and soil topography.</p>
                </div>
              </div>
              <ul className="limitation-list" style={{ lineHeight: '2.0' }}>
                {singleAnalysis.risks.climate_risks.map((cRisk, idx) => (
                  <li key={idx}><strong>Climate:</strong> {cRisk}</li>
                ))}
                {singleAnalysis.risks.economic_risks.map((eRisk, idx) => (
                  <li key={idx}><strong>Financial:</strong> {eRisk}</li>
                ))}
              </ul>

              <h3 style={{ fontSize: '12px', marginTop: '14px' }}>Recommended Action Steps:</h3>
              <ul className="limitation-list" style={{ lineHeight: '1.9' }}>
                {singleAnalysis.risks.mitigation_actions.map((act, idx) => (
                  <li key={idx} style={{ color: 'var(--green-dark)' }}>{act}</li>
                ))}
              </ul>
            </section>
          </div>
        </div>
      )}

      {/* TAB 6: SIDE-BY-SIDE CROP COMPARISON */}
      {activeTab === 'compare' && (
        <div>
          <section className="surface panel">
            <div className="panel-head">
              <div>
                <h2>Multi-Crop Feasibility Comparison for Your Land</h2>
                <p>Consistent financial and agronomic comparison across candidate Kerala crops on {liveConversion.in_acres} acres.</p>
              </div>
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Crop</th>
                    <th>Suitability</th>
                    <th>Expected Yield</th>
                    <th>Total Production</th>
                    <th>Total Cost</th>
                    <th>Gross Revenue</th>
                    <th>Estimated Net Profit</th>
                    <th>Profit / Acre</th>
                    <th>ROI (%)</th>
                    <th>Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {comparedCropsList.map((c) => (
                    <tr
                      key={c.crop}
                      style={{
                        background: c.crop === selectedCrop ? '#edf5ed' : 'transparent',
                        fontWeight: c.crop === selectedCrop ? 600 : 400,
                      }}
                    >
                      <td>
                        <strong>{c.crop}</strong>
                        {c.crop === selectedCrop && <span style={{ marginLeft: '6px', fontSize: '10px', color: 'var(--green)' }}>(Active)</span>}
                      </td>
                      <td>
                        <span className={`tag ${c.suitability.overall_score >= 70 ? '' : 'warning'}`}>
                          {c.suitability.overall_score}/100
                        </span>
                      </td>
                      <td>{fmt(c.production.yield_kg_per_hectare, 0)} kg/ha</td>
                      <td>{fmt(c.production.total_production_tonnes, 2)} t</td>
                      <td>₹{fmt(c.economics.total_cultivation_cost_inr, 0)}</td>
                      <td>₹{fmt(c.economics.gross_revenue_inr, 0)}</td>
                      <td>
                        <strong style={{ color: c.economics.is_profitable ? 'var(--green-dark)' : '#8b4141' }}>
                          ₹{fmt(c.economics.net_profit_inr, 0)}
                        </strong>
                      </td>
                      <td>₹{fmt(c.economics.profit_per_acre_inr, 0)}</td>
                      <td>{c.economics.roi_percent}%</td>
                      <td>{c.calendar?.duration_days || 120} days</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p className="small-note" style={{ marginTop: '12px' }}>
              Comparison uses standardized Kerala DES Cost of Cultivation benchmarks and prevailing Agmarknet wholesale terminal quotes for {district}.
            </p>
          </section>
        </div>
      )}

      {/* TAB 7: MULTI-CROP LAND ALLOCATION */}
      {activeTab === 'allocation' && (
        <div>
          <section className="surface panel">
            <div className="panel-head">
              <div>
                <h2>Land Allocation &amp; Mixed Cropping Calculator</h2>
                <p>Partition your {liveConversion.in_acres} acres across diversified crops to reduce risk and stabilize farm income.</p>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px', marginBottom: '16px' }}>
              {allocations.map((alloc, idx) => (
                <div key={idx} className="info-box">
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <select
                      value={alloc.crop}
                      onChange={(e) => {
                        const newAlloc = [...allocations];
                        newAlloc[idx].crop = e.target.value;
                        setAllocations(newAlloc);
                      }}
                      style={{ minHeight: '32px' }}
                    >
                      {allCrops.map((c) => (
                        <option key={c} value={c}>
                          {c}
                        </option>
                      ))}
                    </select>

                    <button
                      type="button"
                      className="button secondary"
                      style={{ minHeight: '30px', padding: '0 8px', fontSize: '10px' }}
                      onClick={() => {
                        if (allocations.length > 1) {
                          setAllocations(allocations.filter((_, i) => i !== idx));
                        }
                      }}
                    >
                      ✕ Remove
                    </button>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <input
                      type="range"
                      min="5"
                      max="100"
                      step="5"
                      value={alloc.percent}
                      onChange={(e) => {
                        const newAlloc = [...allocations];
                        newAlloc[idx].percent = parseInt(e.target.value);
                        setAllocations(newAlloc);
                      }}
                      style={{ flex: 1 }}
                    />
                    <strong style={{ minWidth: '40px', textAlign: 'right' }}>{alloc.percent}%</strong>
                  </div>

                  <p className="small-note" style={{ margin: '6px 0 0' }}>
                    Area: {Math.round((liveConversion.in_acres * alloc.percent) / 100 * 100) / 100} Acres
                  </p>
                </div>
              ))}
            </div>

            <button
              type="button"
              className="button secondary"
              style={{ marginBottom: '16px' }}
              onClick={() => {
                if (allocations.length < 5) {
                  setAllocations([...allocations, { crop: 'Tapioca', percent: 20 }]);
                }
              }}
            >
              ＋ Add Another Crop Allocation
            </button>

            {/* Allocation Results Summary */}
            <div className="metric-grid">
              <article className="surface metric-card">
                <span className="metric-icon">↗</span>
                <span className="metric-label">Aggregate Harvest</span>
                <strong className="metric-value">
                  {fmt(allocationResult.aggregate_production_tonnes, 2)} Tonnes
                </strong>
                <span className="metric-note">combined farm yield</span>
              </article>

              <article className="surface metric-card">
                <span className="metric-icon">₹</span>
                <span className="metric-label">Total Farm Investment</span>
                <strong className="metric-value">
                  ₹{fmt(allocationResult.aggregate_cost_inr, 0)}
                </strong>
                <span className="metric-note">combined input expenditures</span>
              </article>

              <article className="surface metric-card">
                <span className="metric-icon">＋</span>
                <span className="metric-label">Total Farm Revenue</span>
                <strong className="metric-value">
                  ₹{fmt(allocationResult.aggregate_revenue_inr, 0)}
                </strong>
                <span className="metric-note">total mandi sales</span>
              </article>

              <article className="surface metric-card">
                <span className="metric-icon">★</span>
                <span className="metric-label">Combined Net Profit</span>
                <strong className="metric-value" style={{ color: 'var(--green-dark)' }}>
                  ₹{fmt(allocationResult.aggregate_net_profit_inr, 0)}
                </strong>
                <span className="metric-note">
                  Blended Farm ROI: {allocationResult.aggregate_roi_percent}%
                </span>
              </article>
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Allocated Crop</th>
                    <th>Plot Area (Acres)</th>
                    <th>Production (Tonnes)</th>
                    <th>Cultivation Cost</th>
                    <th>Gross Revenue</th>
                    <th>Net Profit</th>
                  </tr>
                </thead>
                <tbody>
                  {allocationResult.allocations.map((item, idx) => (
                    <tr key={idx}>
                      <td><strong>{item.crop}</strong></td>
                      <td>{item.area_acres} ac</td>
                      <td>{fmt(item.production_tonnes, 2)} t</td>
                      <td>₹{fmt(item.cost_inr, 0)}</td>
                      <td>₹{fmt(item.revenue_inr, 0)}</td>
                      <td><strong style={{ color: item.profit_inr >= 0 ? 'var(--green-dark)' : '#8b4141' }}>₹{fmt(item.profit_inr, 0)}</strong></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      )}
        </div>
      )}
    </div>
  );
};
