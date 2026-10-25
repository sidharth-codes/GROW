export interface DistrictSoilBenchmark {
  district: string;
  representative_tract: string;
  mean_ph: number;
  ph_status: string;
  organic_carbon_percent: number;
  organic_carbon_rating: 'Low' | 'Medium' | 'High';
  available_nitrogen_kg_per_ha: number;
  available_nitrogen_rating: 'Low' | 'Medium' | 'High';
  available_phosphorus_kg_per_ha: number;
  available_phosphorus_rating: 'Low' | 'Medium' | 'High';
  available_potassium_kg_per_ha: number;
  available_potassium_rating: 'Low' | 'Medium' | 'High';
  electrical_conductivity_ds_m: number;
  salinity_status: 'Non-saline' | 'Slightly saline' | 'Moderately saline' | 'Saline (Pokkali)';
  dominant_texture: string;
  dominant_drainage: string;
  source: string;
}

export const DISTRICT_SOIL_BENCHMARKS: Record<string, DistrictSoilBenchmark> = {
  Thiruvananthapuram: {
    district: 'Thiruvananthapuram',
    representative_tract: 'Neyyattinkara / Nedumangad Laterite & Red Loam',
    mean_ph: 5.4,
    ph_status: 'Moderately acidic',
    organic_carbon_percent: 0.85,
    organic_carbon_rating: 'Medium',
    available_nitrogen_kg_per_ha: 240,
    available_nitrogen_rating: 'Low',
    available_phosphorus_kg_per_ha: 28.5,
    available_phosphorus_rating: 'High',
    available_potassium_kg_per_ha: 145,
    available_potassium_rating: 'Medium',
    electrical_conductivity_ds_m: 0.18,
    salinity_status: 'Non-saline',
    dominant_texture: 'Red loam to gravelly laterite',
    dominant_drainage: 'Well drained',
    source: 'Department of Soil Survey & Soil Conservation, Govt. of Kerala - Soil Fertility Map',
  },
  Kollam: {
    district: 'Kollam',
    representative_tract: 'Onattukara coastal sandy & Karunagappally alluvium',
    mean_ph: 5.2,
    ph_status: 'Strongly acidic',
    organic_carbon_percent: 0.48,
    organic_carbon_rating: 'Low',
    available_nitrogen_kg_per_ha: 180,
    available_nitrogen_rating: 'Low',
    available_phosphorus_kg_per_ha: 18.2,
    available_phosphorus_rating: 'Medium',
    available_potassium_kg_per_ha: 95,
    available_potassium_rating: 'Low',
    electrical_conductivity_ds_m: 0.22,
    salinity_status: 'Non-saline',
    dominant_texture: 'Sandy loam to coastal sand',
    dominant_drainage: 'Excessively drained',
    source: 'Soil Health Card Scheme Benchmark - Kerala Soil Survey',
  },
  Pathanamthitta: {
    district: 'Pathanamthitta',
    representative_tract: 'Ranni / Thiruvalla Riverine Alluvium & Midlands',
    mean_ph: 5.5,
    ph_status: 'Moderately acidic',
    organic_carbon_percent: 1.15,
    organic_carbon_rating: 'Medium',
    available_nitrogen_kg_per_ha: 290,
    available_nitrogen_rating: 'Medium',
    available_phosphorus_kg_per_ha: 22.0,
    available_phosphorus_rating: 'Medium',
    available_potassium_kg_per_ha: 160,
    available_potassium_rating: 'Medium',
    electrical_conductivity_ds_m: 0.15,
    salinity_status: 'Non-saline',
    dominant_texture: 'Riverine alluvium & clay loam',
    dominant_drainage: 'Well drained',
    source: 'Kerala Agricultural University Regional Research Station',
  },
  Alappuzha: {
    district: 'Alappuzha',
    representative_tract: 'Kuttanad Kari & Pokkali acid-saline wetland',
    mean_ph: 4.6,
    ph_status: 'Very strongly acidic (Acid sulphate Kari soils)',
    organic_carbon_percent: 2.85,
    organic_carbon_rating: 'High',
    available_nitrogen_kg_per_ha: 360,
    available_nitrogen_rating: 'Medium',
    available_phosphorus_kg_per_ha: 14.5,
    available_phosphorus_rating: 'Medium',
    available_potassium_kg_per_ha: 195,
    available_potassium_rating: 'Medium',
    electrical_conductivity_ds_m: 1.85,
    salinity_status: 'Slightly saline',
    dominant_texture: 'Heavy clay & organic peat',
    dominant_drainage: 'Very poorly drained (requires de-watering bunds)',
    source: 'RRS Moncompu / KAU Kuttanad Soil Study',
  },
  Kottayam: {
    district: 'Kottayam',
    representative_tract: 'Meenachil / Changanassery Brown Hydromorphic & Midland Laterite',
    mean_ph: 5.3,
    ph_status: 'Moderately acidic',
    organic_carbon_percent: 1.28,
    organic_carbon_rating: 'Medium',
    available_nitrogen_kg_per_ha: 275,
    available_nitrogen_rating: 'Low',
    available_phosphorus_kg_per_ha: 26.4,
    available_phosphorus_rating: 'High',
    available_potassium_kg_per_ha: 155,
    available_potassium_rating: 'Medium',
    electrical_conductivity_ds_m: 0.20,
    salinity_status: 'Non-saline',
    dominant_texture: 'Clay to clay loam',
    dominant_drainage: 'Moderately to poorly drained in valleys',
    source: 'Kerala Soil Fertility Status Report - Dept of Soil Survey',
  },
  Idukki: {
    district: 'Idukki',
    representative_tract: 'High Ranges (Udumbanchola / Peerumade) Forest Loam',
    mean_ph: 5.6,
    ph_status: 'Moderately acidic',
    organic_carbon_percent: 2.45,
    organic_carbon_rating: 'High',
    available_nitrogen_kg_per_ha: 420,
    available_nitrogen_rating: 'Medium',
    available_phosphorus_kg_per_ha: 19.8,
    available_phosphorus_rating: 'Medium',
    available_potassium_kg_per_ha: 210,
    available_potassium_rating: 'Medium',
    electrical_conductivity_ds_m: 0.12,
    salinity_status: 'Non-saline',
    dominant_texture: 'Humus rich clay loam & forest loam',
    dominant_drainage: 'Well drained on sloping terrain',
    source: 'Cardamom Research Station Pampadumpara & KAU',
  },
  Ernakulam: {
    district: 'Ernakulam',
    representative_tract: 'Aluva Riverine Alluvium & Vyttila Pokkali coastal tract',
    mean_ph: 5.1,
    ph_status: 'Strongly acidic',
    organic_carbon_percent: 1.40,
    organic_carbon_rating: 'Medium',
    available_nitrogen_kg_per_ha: 310,
    available_nitrogen_rating: 'Medium',
    available_phosphorus_kg_per_ha: 32.0,
    available_phosphorus_rating: 'High',
    available_potassium_kg_per_ha: 180,
    available_potassium_rating: 'Medium',
    electrical_conductivity_ds_m: 2.10,
    salinity_status: 'Saline (Pokkali)',
    dominant_texture: 'Clay in coastal wetland; sandy loam in inland alluvium',
    dominant_drainage: 'Poorly to moderately drained',
    source: 'Rice Research Station Vyttila & Dept of Agriculture',
  },
  Thrissur: {
    district: 'Thrissur',
    representative_tract: 'Thrissur-Ponnani Kole Wetland & Chalakudy Riverine',
    mean_ph: 5.2,
    ph_status: 'Strongly acidic',
    organic_carbon_percent: 2.10,
    organic_carbon_rating: 'High',
    available_nitrogen_kg_per_ha: 340,
    available_nitrogen_rating: 'Medium',
    available_phosphorus_kg_per_ha: 29.5,
    available_phosphorus_rating: 'High',
    available_potassium_kg_per_ha: 175,
    available_potassium_rating: 'Medium',
    electrical_conductivity_ds_m: 0.35,
    salinity_status: 'Non-saline',
    dominant_texture: 'Deep wetland clay',
    dominant_drainage: 'Poorly drained (below MSL in Kole lands)',
    source: 'Kole Land Development Authority & KAU Vellanikkara',
  },
  Palakkad: {
    district: 'Palakkad',
    representative_tract: 'Chittur Black Soil (Vertisol) & Alathur Red Loam',
    mean_ph: 7.2,
    ph_status: 'Neutral to slightly alkaline (Black cotton soil)',
    organic_carbon_percent: 0.65,
    organic_carbon_rating: 'Low',
    available_nitrogen_kg_per_ha: 210,
    available_nitrogen_rating: 'Low',
    available_phosphorus_kg_per_ha: 21.0,
    available_phosphorus_rating: 'Medium',
    available_potassium_kg_per_ha: 320,
    available_potassium_rating: 'High',
    electrical_conductivity_ds_m: 0.45,
    salinity_status: 'Non-saline',
    dominant_texture: 'Black clay (Vertisol) & red loam',
    dominant_drainage: 'Moderately drained to imperfectly drained',
    source: 'RRS Pattambi & Palakkad Soil Testing Lab',
  },
  Malappuram: {
    district: 'Malappuram',
    representative_tract: 'Perinthalmanna / Tirur Laterite & Kole fringe',
    mean_ph: 5.3,
    ph_status: 'Moderately acidic',
    organic_carbon_percent: 0.92,
    organic_carbon_rating: 'Medium',
    available_nitrogen_kg_per_ha: 255,
    available_nitrogen_rating: 'Low',
    available_phosphorus_kg_per_ha: 24.8,
    available_phosphorus_rating: 'Medium',
    available_potassium_kg_per_ha: 135,
    available_potassium_rating: 'Medium',
    electrical_conductivity_ds_m: 0.16,
    salinity_status: 'Non-saline',
    dominant_texture: 'Gravelly laterite to sandy clay loam',
    dominant_drainage: 'Well drained',
    source: 'District Soil Testing Laboratory Malappuram',
  },
  Kozhikode: {
    district: 'Kozhikode',
    representative_tract: 'Quarry Laterite & Coastal Alluvium',
    mean_ph: 5.2,
    ph_status: 'Strongly acidic',
    organic_carbon_percent: 0.88,
    organic_carbon_rating: 'Medium',
    available_nitrogen_kg_per_ha: 230,
    available_nitrogen_rating: 'Low',
    available_phosphorus_kg_per_ha: 27.0,
    available_phosphorus_rating: 'High',
    available_potassium_kg_per_ha: 140,
    available_potassium_rating: 'Medium',
    electrical_conductivity_ds_m: 0.25,
    salinity_status: 'Non-saline',
    dominant_texture: 'Laterite loam & sandy alluvium',
    dominant_drainage: 'Well drained',
    source: 'Indian Institute of Spices Research (IISR) Kozhikode',
  },
  Wayanad: {
    district: 'Wayanad',
    representative_tract: 'Ambalavayal / Mananthavady High Altitude Red Laterite & Humus',
    mean_ph: 5.7,
    ph_status: 'Moderately acidic to near neutral',
    organic_carbon_percent: 2.65,
    organic_carbon_rating: 'High',
    available_nitrogen_kg_per_ha: 390,
    available_nitrogen_rating: 'Medium',
    available_phosphorus_kg_per_ha: 23.5,
    available_phosphorus_rating: 'Medium',
    available_potassium_kg_per_ha: 225,
    available_potassium_rating: 'Medium',
    electrical_conductivity_ds_m: 0.14,
    salinity_status: 'Non-saline',
    dominant_texture: 'Deep clay loam rich in organic matter',
    dominant_drainage: 'Well drained',
    source: 'KAU Regional Agricultural Research Station Ambalavayal',
  },
  Kannur: {
    district: 'Kannur',
    representative_tract: 'Taliparamba Laterite & Ezhome Kaipad coastal acid-saline wetland',
    mean_ph: 4.8,
    ph_status: 'Strongly acidic (Kaipad tidal saline)',
    organic_carbon_percent: 1.35,
    organic_carbon_rating: 'Medium',
    available_nitrogen_kg_per_ha: 280,
    available_nitrogen_rating: 'Medium',
    available_phosphorus_kg_per_ha: 25.0,
    available_phosphorus_rating: 'Medium',
    available_potassium_kg_per_ha: 165,
    available_potassium_rating: 'Medium',
    electrical_conductivity_ds_m: 1.65,
    salinity_status: 'Slightly saline',
    dominant_texture: 'Hydromorphic clay & laterite loam',
    dominant_drainage: 'Poorly drained (Kaipad) to well drained (upland)',
    source: 'College of Agriculture Padannakkad & Dept of Agriculture',
  },
  Kasaragod: {
    district: 'Kasaragod',
    representative_tract: 'Nileshwar / Hosdurg Coastal Sandy & Upland Laterite',
    mean_ph: 5.1,
    ph_status: 'Strongly acidic',
    organic_carbon_percent: 0.72,
    organic_carbon_rating: 'Low',
    available_nitrogen_kg_per_ha: 215,
    available_nitrogen_rating: 'Low',
    available_phosphorus_kg_per_ha: 28.0,
    available_phosphorus_rating: 'High',
    available_potassium_kg_per_ha: 120,
    available_potassium_rating: 'Medium',
    electrical_conductivity_ds_m: 0.19,
    salinity_status: 'Non-saline',
    dominant_texture: 'Gravelly laterite & coastal sand',
    dominant_drainage: 'Well drained',
    source: 'Central Plantation Crops Research Institute (CPCRI) Kasaragod',
  },
};

export interface SoilTestEvaluation {
  ph_rating: string;
  n_rating: 'Low' | 'Medium' | 'High';
  p_rating: 'Low' | 'Medium' | 'High';
  k_rating: 'Low' | 'Medium' | 'High';
  oc_rating: 'Low' | 'Medium' | 'High';
  ec_rating: 'Normal' | 'Critical';
  soil_health_score: number; // 0 - 100
  lime_recommendation_kg_per_ha: number;
  fertilizer_adjustment_advice: string[];
}

export function evaluateFarmerSoilTest(
  ph: number,
  n?: number | null,
  p?: number | null,
  k?: number | null,
  oc?: number | null,
  ec?: number | null
): SoilTestEvaluation {
  let phRating = 'Optimal (Near neutral)';
  let limeReq = 0;
  if (ph < 4.5) {
    phRating = 'Extremely acidic (Aluminium toxicity risk)';
    limeReq = 800;
  } else if (ph < 5.5) {
    phRating = 'Strongly acidic (Lime application advised)';
    limeReq = 500;
  } else if (ph <= 7.0) {
    phRating = 'Slightly acidic to neutral (Optimal for most Kerala crops)';
    limeReq = 0;
  } else {
    phRating = 'Alkaline (Vertisol characteristic)';
    limeReq = 0;
  }

  const nVal = n != null ? n : 260;
  const nRating: 'Low' | 'Medium' | 'High' = nVal < 280 ? 'Low' : nVal <= 560 ? 'Medium' : 'High';

  const pVal = p != null ? p : 22;
  const pRating: 'Low' | 'Medium' | 'High' = pVal < 10 ? 'Low' : pVal <= 25 ? 'Medium' : 'High';

  const kVal = k != null ? k : 150;
  const kRating: 'Low' | 'Medium' | 'High' = kVal < 110 ? 'Low' : kVal <= 280 ? 'Medium' : 'High';

  const ocVal = oc != null ? oc : 1.2;
  const ocRating: 'Low' | 'Medium' | 'High' = ocVal < 0.75 ? 'Low' : ocVal <= 1.5 ? 'Medium' : 'High';

  const ecVal = ec != null ? ec : 0.25;
  const ecRating: 'Normal' | 'Critical' = ecVal > 1.5 ? 'Critical' : 'Normal';

  const advice: string[] = [];
  if (limeReq > 0) {
    advice.push(`Apply agricultural lime (CaCO3) or dolomite @ ${limeReq} kg/ha 2-3 weeks before planting to correct acidity.`);
  }
  if (nRating === 'Low') {
    advice.push('Available Nitrogen is low: augment basal dose with vermicompost / cowdung and split urea applications.');
  }
  if (pRating === 'High') {
    advice.push('Available Phosphorus is high: reduce chemical phosphatic fertilizer (DAP/Factamfos) by 25% to prevent nutrient lockup.');
  }
  if (kRating === 'Low') {
    advice.push('Available Potassium is low: ensure full Muriate of Potash (MOP) dosage, critical for bunch development, fruit size, and disease resistance.');
  }
  if (ocRating === 'Low') {
    advice.push('Organic carbon is low (<0.75%): incorporate green manure crops (Daincha/Sunn hemp) or coir pith compost @ 5-10 tonnes/ha.');
  }
  if (ecRating === 'Critical') {
    advice.push('Electrical conductivity exceeds 1.5 dS/m: soil exhibits salinity stress. Ensure adequate pre-monsoon flushing of fields.');
  }

  // Calculate composite soil health score
  let score = 75;
  if (ph >= 5.5 && ph <= 7.0) score += 10;
  else if (ph < 5.0) score -= 15;

  if (ocRating === 'High') score += 10;
  else if (ocRating === 'Low') score -= 10;

  if (ecRating === 'Critical') score -= 20;

  score = Math.max(20, Math.min(100, score));

  return {
    ph_rating: phRating,
    n_rating: nRating,
    p_rating: pRating,
    k_rating: kRating,
    oc_rating: ocRating,
    ec_rating: ecRating,
    soil_health_score: score,
    lime_recommendation_kg_per_ha: limeReq,
    fertilizer_adjustment_advice: advice,
  };
}
