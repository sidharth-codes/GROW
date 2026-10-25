export interface CostItemBreakdown {
  category: string;
  cost_inr_per_hectare: number;
  share_percent: number;
  description: string;
}

export interface CropCostStructure {
  crop: string;
  season?: string;
  reference_year: string;
  source: string;
  accounting_basis: 'Cost A (Paid-out costs)' | 'Reported Input Cost' | 'Comprehensive Cost C';
  total_cost_inr_per_hectare: number;
  breakdown: CostItemBreakdown[];
  district_wage_adjustment_factor?: Record<string, number>;
  source_notes: string;
}

export const CULTIVATION_COST_BENCHMARKS: Record<string, CropCostStructure> = {
  Rice: {
    crop: 'Rice',
    season: 'Autumn / Winter',
    reference_year: '2023-24',
    source: 'Kerala Department of Economics & Statistics (DES) Cost of Cultivation Report 2023-24',
    accounting_basis: 'Reported Input Cost',
    total_cost_inr_per_hectare: 80542,
    breakdown: [
      { category: 'Land Preparation & Tractor Hire', cost_inr_per_hectare: 11200, share_percent: 13.9, description: 'Ploughing, puddle levelling, bund trimming' },
      { category: 'Seeds & Nursery Raising', cost_inr_per_hectare: 6800, share_percent: 8.4, description: 'High-yielding certified seed (80 kg/ha) & nursery maintenance' },
      { category: 'Fertilizers, Lime & Organic Manure', cost_inr_per_hectare: 12500, share_percent: 15.5, description: 'Urea, Factamfos/DAP, MOP, agricultural lime application' },
      { category: 'Human Labour (Transplanting & Weeding)', cost_inr_per_hectare: 33400, share_percent: 41.5, description: 'Transplanting crew, manual weeding, interculture' },
      { category: 'Irrigation & Drainage Management', cost_inr_per_hectare: 3800, share_percent: 4.7, description: 'Pumping electricity/fuel charges, dewatering in wetlands' },
      { category: 'Plant Protection & Biocontrol', cost_inr_per_hectare: 3100, share_percent: 3.8, description: 'Bio-pesticides, neem spray, Trichoderma application' },
      { category: 'Combined Harvester & Threshing', cost_inr_per_hectare: 7200, share_percent: 8.9, description: 'Mechanical harvester hire & winnowing charges' },
      { category: 'Transport & Gunny Bags', cost_inr_per_hectare: 2542, share_percent: 3.2, description: 'Bagging, farm-gate to procurement centre haulage' },
    ],
    source_notes: 'Statewide average across major paddy tracts (Palakkad, Kuttanad, Kole). Does not include rent on owned land or managerial allowance.',
  },
  Coconut: {
    crop: 'Coconut',
    season: 'Annual (Bearing palms)',
    reference_year: '2023-24',
    source: 'Kerala Department of Economics & Statistics (DES) 2023-24 Report',
    accounting_basis: 'Reported Input Cost',
    total_cost_inr_per_hectare: 97530,
    breakdown: [
      { category: 'Basin Opening & Mulching', cost_inr_per_hectare: 14600, share_percent: 15.0, description: 'Annual basin opening, green leaf mulching, weeding' },
      { category: 'Chemical Fertilizers & Organic Manures', cost_inr_per_hectare: 22800, share_percent: 23.4, description: 'NPK mixture (500:320:1200g/palm), cowdung & coir pith compost' },
      { category: 'Harvesting & Palm Climbing Charges', cost_inr_per_hectare: 32500, share_percent: 33.3, description: 'Climbing charges per palm (6-8 harvest rounds/year @ ₹40-50/palm)' },
      { category: 'Irrigation & Basin Water Management', cost_inr_per_hectare: 11200, share_percent: 11.5, description: 'Drip system maintenance / hose basin irrigation during dry months' },
      { category: 'Plant Protection & Crown Cleaning', cost_inr_per_hectare: 9400, share_percent: 9.6, description: 'Crown cleaning, rhinoceros beetle hooking, Bordeaux paste application' },
      { category: 'Transport, Dehusking & Marketing', cost_inr_per_hectare: 7030, share_percent: 7.2, description: 'Dehusking labour and transportation to copra dryers/mandi' },
    ],
    source_notes: 'Based on standard adult density of 175 palms/hectare in bearing orchards.',
  },
  Banana: {
    crop: 'Banana',
    season: 'Annual (Nendran)',
    reference_year: '2023-24',
    source: 'Kerala Department of Economics & Statistics (DES) 2023-24 Report',
    accounting_basis: 'Reported Input Cost',
    total_cost_inr_per_hectare: 260472,
    breakdown: [
      { category: 'Land Preparation & Pit Digging', cost_inr_per_hectare: 24800, share_percent: 9.5, description: 'Deep ploughing, pit excavation (0.5m x 0.5m) for 2500 plants/ha' },
      { category: 'Tissue Culture / Sword Suckers', cost_inr_per_hectare: 35000, share_percent: 13.4, description: 'Quality certified disease-free suckers @ ₹14/unit' },
      { category: 'Fertilizers, Lime & Cattle Manure', cost_inr_per_hectare: 48600, share_percent: 18.7, description: 'High potassium nutrition (400g K2O/plant) + organic cowdung manure' },
      { category: 'Bamboo Propping Poles & Staking', cost_inr_per_hectare: 38200, share_percent: 14.7, description: 'Two bamboo poles per fruiting pseudostem to prevent wind lodging' },
      { category: 'Human Labour (Weeding & Earthing Up)', cost_inr_per_hectare: 56400, share_percent: 21.7, description: 'Periodic de-suckering, leaf removal, earthing up, trenching' },
      { category: 'Irrigation & Fertigation', cost_inr_per_hectare: 18600, share_percent: 7.1, description: 'Frequent drip / flood irrigation through dry winter-summer months' },
      { category: 'Plant Protection (Weevil & Sigatoka)', cost_inr_per_hectare: 16800, share_percent: 6.5, description: 'Pseudostem injection, mineral oil spray, bunch sleeves' },
      { category: 'Harvesting, Bunch Cutting & Transport', cost_inr_per_hectare: 22072, share_percent: 8.5, description: 'Bunch cutting, foam padding, local mandi transport' },
    ],
    source_notes: 'Reflects intensive Nendran cultivation at 2,500 plants/hectare.',
  },
  'Black pepper': {
    crop: 'Black pepper',
    season: 'Annual (Bearing vines)',
    reference_year: '2023-24',
    source: 'Kerala Department of Economics & Statistics (DES) 2023-24 Report',
    accounting_basis: 'Reported Input Cost',
    total_cost_inr_per_hectare: 98183,
    breakdown: [
      { category: 'Standard Tree Lopping & Tying Vines', cost_inr_per_hectare: 18400, share_percent: 18.7, description: 'Pruning support tree shade branches, tying runner shoots' },
      { category: 'Organic Compost, Lime & Fertilizers', cost_inr_per_hectare: 21600, share_percent: 22.0, description: 'Neem cake, dolomite lime, balanced NPK split doses' },
      { category: 'Phytophthora & Plant Protection Spray', cost_inr_per_hectare: 14800, share_percent: 15.1, description: 'Pre- and post-monsoon 1% Bordeaux mixture spraying and drenching' },
      { category: 'Weeding, Soil Mulching & Basin Care', cost_inr_per_hectare: 12800, share_percent: 13.0, description: 'Slope terracing, ring weeding, biological mulch spreading' },
      { category: 'Harvesting Spike Picking (Manual)', cost_inr_per_hectare: 24200, share_percent: 24.6, description: 'Skilled bamboo ladder climbing for berry spike harvesting' },
      { category: 'Threshing, Drying & Cleaning', cost_inr_per_hectare: 6383, share_percent: 6.5, description: 'Mechanical thresher hire, sun drying on clean tarpaulins, winnowing' },
    ],
    source_notes: 'Standard 1,100 vines/hectare on live support trees in high/midland regions (Wayanad, Idukki).',
  },
  Rubber: {
    crop: 'Rubber',
    season: 'Annual (Mature tapping grove)',
    reference_year: '2023-24',
    source: 'Rubber Board of India & Kerala DES Estimates 2023-24',
    accounting_basis: 'Reported Input Cost',
    total_cost_inr_per_hectare: 114500,
    breakdown: [
      { category: 'Tapping Labour (Daily / Alternate Day)', cost_inr_per_hectare: 58000, share_percent: 50.7, description: 'Skilled tapper wages (120-140 tapping days/year)' },
      { category: 'Rainguard Material & Fixing', cost_inr_per_hectare: 14200, share_percent: 12.4, description: 'Polythene rainguards, synthetic adhesive, stapling before monsoon' },
      { category: 'Fertilizers & Soil Conditioning', cost_inr_per_hectare: 16800, share_percent: 14.7, description: 'Rubber mixture (NPK 10:10:10 or 12:12:12), rock phosphate' },
      { category: 'Disease Control (Phytophthora Aerial/Tractor Spray)', cost_inr_per_hectare: 11400, share_percent: 10.0, description: 'Micron sprayer Bordeaux/copper oxychloride spray for abnormal leaf fall' },
      { category: 'Latex Coagulation & Sheet Processing', cost_inr_per_hectare: 9600, share_percent: 8.4, description: 'Formic acid, coagulating pans, roller machine maintenance, smokehouse firewood' },
      { category: 'Weeding & Cover Crop Upkeep', cost_inr_per_hectare: 4500, share_percent: 3.9, description: 'Slash weeding of undergrowth, Mucuna cover crop trimming' },
    ],
    source_notes: 'Calculated for mature stand of 450 tapping trees/hectare.',
  },
  Tapioca: {
    crop: 'Tapioca',
    season: 'Main crop (Monsoon)',
    reference_year: '2023-24',
    source: 'Kerala Department of Economics & Statistics (DES) 2023-24 Report',
    accounting_basis: 'Reported Input Cost',
    total_cost_inr_per_hectare: 174039,
    breakdown: [
      { category: 'Land Preparation & Mound/Ridge Formation', cost_inr_per_hectare: 26500, share_percent: 15.2, description: 'Deep disc ploughing and manual mound construction' },
      { category: 'Stem Cuttings (Setts) & Planting', cost_inr_per_hectare: 14200, share_percent: 8.2, description: 'Quality stem bundles and sett planting labour (10,000 plants/ha)' },
      { category: 'Fertilizers & Potash Nutrition', cost_inr_per_hectare: 34800, share_percent: 20.0, description: 'High potash doses (100 kg K2O/ha), urea, and compost' },
      { category: 'Weeding, Earthing Up & Branch Removal', cost_inr_per_hectare: 46200, share_percent: 26.5, description: 'Two rounds of manual weeding and earthing up around mounds' },
      { category: 'Plant Protection & Insect Management', cost_inr_per_hectare: 8400, share_percent: 4.8, description: 'Whitefly management to prevent Cassava Mosaic Virus' },
      { category: 'Harvesting & Manual Uprooting', cost_inr_per_hectare: 32600, share_percent: 18.7, description: 'Tuber digging, stem separation, sorting and field-side loading' },
      { category: 'Transportation to Chips Mill/Market', cost_inr_per_hectare: 11339, share_percent: 6.5, description: 'Trucking charges for high-moisture perishable tuber load' },
    ],
    source_notes: 'Covers irrigated and rainfed upland cassava production at 10,000 stands/ha.',
  },
  Ginger: {
    crop: 'Ginger',
    season: 'Monsoon (Rainfed)',
    reference_year: '2023-24',
    source: 'Kerala Department of Economics & Statistics (DES) 2023-24 Report',
    accounting_basis: 'Reported Input Cost',
    total_cost_inr_per_hectare: 273571,
    breakdown: [
      { category: 'Land Preparation & Raised Bed Construction', cost_inr_per_hectare: 32000, share_percent: 11.7, description: 'Fine tilth preparation, beds 1m width, 15cm height with drainage channels' },
      { category: 'Seed Rhizomes (High Cost Item)', cost_inr_per_hectare: 76000, share_percent: 27.8, description: 'Disease-free seed rhizomes (1,500-1,800 kg/ha @ ₹45-50/kg)' },
      { category: 'Seed Treatment & Trichoderma Bio-inoculant', cost_inr_per_hectare: 8500, share_percent: 3.1, description: 'Rhizome soaking in bio-agent solution against Pythium soft rot' },
      { category: 'Green Leaf Mulching (3 Applications)', cost_inr_per_hectare: 38400, share_percent: 14.0, description: 'Total 22 tonnes/hectare green tree loppings for moisture and soil cooling' },
      { category: 'Manures & Balanced Fertilizer Schedule', cost_inr_per_hectare: 42600, share_percent: 15.6, description: 'Farmyard manure (25 t/ha), neem cake (2 t/ha), NPK 75:50:50 kg/ha' },
      { category: 'Weeding, Earthing Up & Drainage', cost_inr_per_hectare: 39200, share_percent: 14.3, description: 'Clearing drainage trenches to prevent water stagnation' },
      { category: 'Harvesting, Washing & Cleaning', cost_inr_per_hectare: 27400, share_percent: 10.0, description: 'Careful spade digging to avoid bruising rhizomes, water jet cleaning' },
      { category: 'Grading, Packaging & Mandi Transport', cost_inr_per_hectare: 9471, share_percent: 3.5, description: 'Crates, packaging in mesh sacks, transport to wholesale terminal' },
    ],
    source_notes: 'High-capital crop due to heavy seed-rhizome requirement and multiple mulching cycles.',
  },
  Turmeric: {
    crop: 'Turmeric',
    season: 'Monsoon (May - Jan)',
    reference_year: '2023-24',
    source: 'Kerala Agricultural University & DES Reports 2023-24',
    accounting_basis: 'Reported Input Cost',
    total_cost_inr_per_hectare: 212400,
    breakdown: [
      { category: 'Bed Preparation & Soil Tillage', cost_inr_per_hectare: 26000, share_percent: 12.2, description: 'Raised bed formation and basal incorporation of manure' },
      { category: 'Seed Rhizomes', cost_inr_per_hectare: 54000, share_percent: 25.4, description: 'Certified mother/finger rhizomes (2,000 kg/ha)' },
      { category: 'Green Leaf Mulching', cost_inr_per_hectare: 28000, share_percent: 13.2, description: 'Two rounds of forest leaf mulching' },
      { category: 'Organic Manures & Fertilizers', cost_inr_per_hectare: 36400, share_percent: 17.1, description: 'Compost, poultry manure, NPK 60:50:120 kg/ha' },
      { category: 'Weeding & Intercultural Care', cost_inr_per_hectare: 32000, share_percent: 15.1, description: 'Periodic weeding and earthing up of rhizome mounds' },
      { category: 'Harvesting & De-leafing', cost_inr_per_hectare: 25000, share_percent: 11.8, description: 'Manual digging after foliage withers' },
      { category: 'Cleaning, Boiling, Polishing & Transport', cost_inr_per_hectare: 11000, share_percent: 5.2, description: 'Initial post-harvest cure and delivery' },
    ],
    source_notes: 'Statewide benchmark for commercial high-curcumin turmeric cultivation.',
  },
  Groundnut: {
    crop: 'Groundnut',
    season: 'Post-monsoon (Rainfed/Irrigated)',
    reference_year: '2023-24',
    source: 'CACP & KAU Regional Station Palakkad Benchmark 2023-24',
    accounting_basis: 'Reported Input Cost',
    total_cost_inr_per_hectare: 68500,
    breakdown: [
      { category: 'Tillage & Sowing Seedbed', cost_inr_per_hectare: 10500, share_percent: 15.3, description: 'Harrowing, planking, furrow opening' },
      { category: 'Certified Kernel Seed & Inoculation', cost_inr_per_hectare: 14200, share_percent: 20.7, description: 'Kernels (120 kg/ha) treated with Rhizobium culture' },
      { category: 'Fertilizers, Gypsum & Micro-nutrients', cost_inr_per_hectare: 13800, share_percent: 20.1, description: 'NPK 10:25:0 kg/ha + Gypsum @ 400 kg/ha at pegging' },
      { category: 'Weeding & Hoeing', cost_inr_per_hectare: 12000, share_percent: 17.5, description: 'Shallow weeding prior to peg entry' },
      { category: 'Irrigation & Plant Protection', cost_inr_per_hectare: 6200, share_percent: 9.1, description: 'Supplementary moisture and leaf miner management' },
      { category: 'Pod Harvesting & Stripping', cost_inr_per_hectare: 8800, share_percent: 12.8, description: 'Manual vine lifting and pod stripping' },
      { category: 'Sun Drying & Cleaning', cost_inr_per_hectare: 3000, share_percent: 4.4, description: 'Drying pods to <9% safe moisture content' },
    ],
    source_notes: 'Calibrated for Palakkad Chittur groundnut basin.',
  },
  Vegetables: {
    crop: 'Vegetables',
    season: 'Tri-seasonal (Intensive)',
    reference_year: '2023-24',
    source: 'State Horticulture Mission & KAU Package of Practices 2023-24',
    accounting_basis: 'Reported Input Cost',
    total_cost_inr_per_hectare: 142000,
    breakdown: [
      { category: 'Land Preparation & Bed Mulching', cost_inr_per_hectare: 18500, share_percent: 13.0, description: 'Rotavator ploughing, raised bed layout, silver-black plastic mulch' },
      { category: 'Hybrid Seeds / Pro-tray Seedlings', cost_inr_per_hectare: 16800, share_percent: 11.8, description: 'High-yielding F1 hybrid seedlings from nursery pro-trays' },
      { category: 'Drip Irrigation & Fertigation Pipes', cost_inr_per_hectare: 14200, share_percent: 10.0, description: 'Drip lateral lines and venturi injector upkeep' },
      { category: 'Staking & Trellising (Pandals)', cost_inr_per_hectare: 21500, share_percent: 15.1, description: 'Bamboo stakes and nylon netting for climbers (bitter gourd, cowpea)' },
      { category: 'Water Soluble Fertilizers & Organic Cake', cost_inr_per_hectare: 26000, share_percent: 18.3, description: '19:19:19 fertigation, calcium nitrate, neem cake' },
      { category: 'Integrated Pest Management (Pheromone/Biocontrol)', cost_inr_per_hectare: 12800, share_percent: 9.0, description: 'Pheromone traps, fruit fly lures, Pseudomonas foliar sprays' },
      { category: 'Frequent Staggered Harvesting', cost_inr_per_hectare: 24500, share_percent: 17.3, description: 'Harvesting every 3-4 days over an 8-week production window' },
      { category: 'Sorting, Crates & Daily Mandi Delivery', cost_inr_per_hectare: 7700, share_percent: 5.4, description: 'Plastic field crates and delivery to VFPCK / wholesale mandi' },
    ],
    source_notes: 'Composite cost model representing mixed intensive vegetable cropping (Bhindi, Cowpea, Brinjal, Cucurbits).',
  },
};
