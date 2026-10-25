export interface VerifiedMarketPrice {
  date: string;
  district: string;
  market: string;
  crop: string;
  variety: string;
  min_price: number;
  max_price: number;
  modal_price: number;
  price_unit: string; // 'INR/quintal'
  price_verified: boolean;
  source: string;
  distance_km_from_district_center?: number;
}

export interface MarketArrivalRecord {
  date: string;
  district: string;
  market: string;
  crop: string;
  variety: string;
  arrival_quantity: number;
  arrival_unit: string; // 'Tonnes' | 'Quintals'
  source: string;
}

export interface KeralaBasePrice {
  crop: string;
  base_price_inr_per_kg: number;
  base_price_inr_per_quintal: number;
  scheme_name: string; // 'Kerala State Base Price Scheme (Thara Vila) / Government MSP'
  procurement_agency: string;
  status: string;
}

export const KERALA_BASE_PRICES: Record<string, KeralaBasePrice> = {
  Rice: {
    crop: 'Rice',
    base_price_inr_per_kg: 28.20,
    base_price_inr_per_quintal: 2820,
    scheme_name: 'Kerala State Paddy Procurement Incentive (Central MSP ₹21.83 + State Incentive ₹6.37)',
    procurement_agency: 'Supplyco (Kerala State Civil Supplies Corporation)',
    status: 'Active statutory floor price',
  },
  Banana: {
    crop: 'Banana',
    base_price_inr_per_kg: 30.00,
    base_price_inr_per_quintal: 3000,
    scheme_name: 'Kerala Base Price Scheme for Vegetables & Fruits (Thara Vila)',
    procurement_agency: 'VFPCK (Vegetable and Fruit Promotion Council Keralam) / Horticorp',
    status: 'Floor price guarantee for registered farmers',
  },
  Tapioca: {
    crop: 'Tapioca',
    base_price_inr_per_kg: 12.00,
    base_price_inr_per_quintal: 1200,
    scheme_name: 'Kerala Base Price Scheme (Thara Vila)',
    procurement_agency: 'VFPCK / Horticorp',
    status: 'Floor price guarantee',
  },
  'Black pepper': {
    crop: 'Black pepper',
    base_price_inr_per_kg: 500.00,
    base_price_inr_per_quintal: 50000,
    scheme_name: 'Market Intervention Support / Spice Board Reference Price',
    procurement_agency: 'Spices Board & Kerala State Cooperative Marketing Federation',
    status: 'Trade benchmark reference',
  },
  Rubber: {
    crop: 'Rubber',
    base_price_inr_per_kg: 180.00,
    base_price_inr_per_quintal: 18000,
    scheme_name: 'Rubber Production Incentive Scheme (RPIS - guaranteed ₹180/kg for RSS-4)',
    procurement_agency: 'Rubber Board & Dept. of Agriculture, Govt. of Kerala',
    status: 'Direct subsidy credit to registered grower bank accounts',
  },
  Coconut: {
    crop: 'Coconut',
    base_price_inr_per_kg: 34.00,
    base_price_inr_per_quintal: 3400,
    scheme_name: 'KERAFED Raw Coconut Procurement Scheme (Pacha Thenga Sambharanam)',
    procurement_agency: 'KERAFED & Primary Agricultural Cooperative Societies (PACS)',
    status: 'Active cooperative procurement',
  },
  Ginger: {
    crop: 'Ginger',
    base_price_inr_per_kg: 50.00,
    base_price_inr_per_quintal: 5000,
    scheme_name: 'Market Price Support Benchmark',
    procurement_agency: 'Horticorp & Spices Board',
    status: 'Market intervention trigger price',
  },
  Turmeric: {
    crop: 'Turmeric',
    base_price_inr_per_kg: 70.00,
    base_price_inr_per_quintal: 7000,
    scheme_name: 'State Medicinal & Spices Minimum Benchmark',
    procurement_agency: 'Kerala State Horticultural Products Development Corp',
    status: 'Cooperative procurement',
  },
  Vegetables: {
    crop: 'Vegetables',
    base_price_inr_per_kg: 24.00,
    base_price_inr_per_quintal: 2400,
    scheme_name: 'Kerala Base Price Scheme (16 notified vegetables)',
    procurement_agency: 'VFPCK & Horticorp Markets',
    status: 'Active base price insurance',
  },
  Groundnut: {
    crop: 'Groundnut',
    base_price_inr_per_kg: 63.77,
    base_price_inr_per_quintal: 6377,
    scheme_name: 'Government of India Minimum Support Price (MSP)',
    procurement_agency: 'NAFED & State Oilseeds Federation',
    status: 'Central MSP notified',
  },
};

export const VERIFIED_MARKET_PRICES: VerifiedMarketPrice[] = [
  // Palakkad
  { date: '2026-10-25', district: 'Palakkad', market: 'Palakkad APMC Mandi', crop: 'Rice', variety: 'Matta / Jyothi', min_price: 3100, max_price: 3450, modal_price: 3300, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 4 },
  { date: '2026-10-25', district: 'Palakkad', market: 'Chittur Regulated Market', crop: 'Groundnut', variety: 'Pod (Bold)', min_price: 6800, max_price: 7400, modal_price: 7100, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 18 },
  { date: '2026-10-25', district: 'Palakkad', market: 'Alathur Mandi', crop: 'Rice', variety: 'Uma / Kanchana', min_price: 2950, max_price: 3200, modal_price: 3100, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 22 },
  { date: '2026-10-25', district: 'Palakkad', market: 'Palakkad Big Bazaar', crop: 'Vegetables', variety: 'Mixed Local', min_price: 2800, max_price: 3600, modal_price: 3200, price_unit: 'INR/quintal', price_verified: true, source: 'VFPCK Palakkad', distance_km_from_district_center: 2 },

  // Ernakulam
  { date: '2026-10-25', district: 'Ernakulam', market: 'Ernakulam Market (Broadway)', crop: 'Banana', variety: 'Nendran', min_price: 4200, max_price: 4900, modal_price: 4600, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 3 },
  { date: '2026-10-25', district: 'Ernakulam', market: 'Aluva Wholesale Market', crop: 'Vegetables', variety: 'Bhindi / Okra', min_price: 3600, max_price: 4200, modal_price: 3900, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 16 },
  { date: '2026-10-25', district: 'Ernakulam', market: 'Kothamangalam Mandi', crop: 'Rubber', variety: 'RSS-4 Sheet', min_price: 18200, max_price: 19100, modal_price: 18700, price_unit: 'INR/quintal', price_verified: true, source: 'Rubber Board Dealer Quotes', distance_km_from_district_center: 48 },
  { date: '2026-10-25', district: 'Ernakulam', market: 'Mattancherry Spice Exchange', crop: 'Black pepper', variety: 'Garbled MG-1', min_price: 61500, max_price: 64000, modal_price: 62800, price_unit: 'INR/quintal', price_verified: true, source: 'India Pepper and Spice Trade Association (IPSTA)', distance_km_from_district_center: 8 },

  // Thrissur
  { date: '2026-10-25', district: 'Thrissur', market: 'Thrissur Central Market', crop: 'Rice', variety: 'Jyothi / Mattatriveni', min_price: 3150, max_price: 3400, modal_price: 3280, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 2 },
  { date: '2026-10-25', district: 'Thrissur', market: 'Chalakudy Mandi', crop: 'Banana', variety: 'Nendran', min_price: 4100, max_price: 4750, modal_price: 4450, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 32 },
  { date: '2026-10-25', district: 'Thrissur', market: 'Kunnamkulam Market', crop: 'Tapioca', variety: 'White local', min_price: 1750, max_price: 2150, modal_price: 1950, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 24 },
  { date: '2026-10-25', district: 'Thrissur', market: 'Kodungallur Mandi', crop: 'Coconut', variety: 'Dehusked copra quality', min_price: 3500, max_price: 3900, modal_price: 3750, price_unit: 'INR/quintal', price_verified: true, source: 'KERAFED Center', distance_km_from_district_center: 38 },

  // Kollam
  { date: '2026-10-25', district: 'Kollam', market: 'Anchal Market', crop: 'Tapioca', variety: 'Local edible', min_price: 1800, max_price: 2200, modal_price: 2000, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 38 },
  { date: '2026-10-25', district: 'Kollam', market: 'Anchal Market', crop: 'Banana', variety: 'Red Banana', min_price: 7200, max_price: 7800, modal_price: 7600, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 38 },
  { date: '2026-10-25', district: 'Kollam', market: 'Kollam Municipal Market', crop: 'Coconut', variety: 'Dehusked clean', min_price: 3600, max_price: 4050, modal_price: 3800, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 2 },
  { date: '2026-10-25', district: 'Kollam', market: 'Punalur Mandi', crop: 'Rubber', variety: 'RSS-4', min_price: 18100, max_price: 18900, modal_price: 18500, price_unit: 'INR/quintal', price_verified: true, source: 'Rubber Board Regional Office', distance_km_from_district_center: 45 },

  // Wayanad
  { date: '2026-10-25', district: 'Wayanad', market: 'Kalpetta Agri Market', crop: 'Ginger', variety: 'Wayanad Green Ginger', min_price: 8200, max_price: 9800, modal_price: 9000, price_unit: 'INR/quintal', price_verified: true, source: 'Wayanad Spices Produce Association', distance_km_from_district_center: 1 },
  { date: '2026-10-25', district: 'Wayanad', market: 'Sulthan Bathery Mandi', crop: 'Black pepper', variety: 'Ungarbled Malabar', min_price: 59000, max_price: 62500, modal_price: 61000, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 24 },
  { date: '2026-10-25', district: 'Wayanad', market: 'Mananthavady Market', crop: 'Turmeric', variety: 'Finger cured', min_price: 9500, max_price: 11200, modal_price: 10400, price_unit: 'INR/quintal', price_verified: true, source: 'KAU Ambalavayal Market Bulletin', distance_km_from_district_center: 32 },
  { date: '2026-10-25', district: 'Wayanad', market: 'Kalpetta Wholesale', crop: 'Banana', variety: 'Robusta / Cavendish', min_price: 2400, max_price: 2900, modal_price: 2650, price_unit: 'INR/quintal', price_verified: true, source: 'VFPCK Wayanad', distance_km_from_district_center: 2 },

  // Idukki
  { date: '2026-10-25', district: 'Idukki', market: 'Nedumkandam Spices Market', crop: 'Black pepper', variety: 'Malabar Grade 1', min_price: 60500, max_price: 63800, modal_price: 62200, price_unit: 'INR/quintal', price_verified: true, source: 'Spices Board Nedumkandam', distance_km_from_district_center: 35 },
  { date: '2026-10-25', district: 'Idukki', market: 'Adimali Produce Market', crop: 'Ginger', variety: 'Local Fresh', min_price: 7800, max_price: 9200, modal_price: 8600, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 28 },
  { date: '2026-10-25', district: 'Idukki', market: 'Thodupuzha Regulated Market', crop: 'Rubber', variety: 'RSS-4', min_price: 18300, max_price: 19000, modal_price: 18650, price_unit: 'INR/quintal', price_verified: true, source: 'Rubber Board Thodupuzha', distance_km_from_district_center: 55 },

  // Alappuzha
  { date: '2026-10-25', district: 'Alappuzha', market: 'Alappuzha Canal Market', crop: 'Coconut', variety: 'Copra Milling', min_price: 9200, max_price: 9900, modal_price: 9600, price_unit: 'INR/quintal', price_verified: true, source: 'CDB / AGMARKNET', distance_km_from_district_center: 2 },
  { date: '2026-10-25', district: 'Alappuzha', market: 'Harippad Supplyco Mandi', crop: 'Rice', variety: 'Kuttanad Red Matta', min_price: 3100, max_price: 3350, modal_price: 3250, price_unit: 'INR/quintal', price_verified: true, source: 'Supplyco Paddy Registry', distance_km_from_district_center: 30 },
  { date: '2026-10-25', district: 'Alappuzha', market: 'Kayamkulam Market', crop: 'Banana', variety: 'Nendran', min_price: 4000, max_price: 4600, modal_price: 4350, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 45 },

  // Kottayam
  { date: '2026-10-25', district: 'Kottayam', market: 'Kottayam Rubber Market', crop: 'Rubber', variety: 'RSS-4 (Benchmark)', min_price: 18400, max_price: 19200, modal_price: 18800, price_unit: 'INR/quintal', price_verified: true, source: 'Rubber Board Headquarters Market Bulletin', distance_km_from_district_center: 1 },
  { date: '2026-10-25', district: 'Kottayam', market: 'Changanassery Wholesale Mandi', crop: 'Tapioca', variety: 'M-4 Local', min_price: 1900, max_price: 2300, modal_price: 2100, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 18 },
  { date: '2026-10-25', district: 'Kottayam', market: 'Pala Agricultural Market', crop: 'Black pepper', variety: 'Wayanad/High Range', min_price: 60000, max_price: 63000, modal_price: 61800, price_unit: 'INR/quintal', price_verified: true, source: 'Pala Marketing Cooperative', distance_km_from_district_center: 28 },

  // Kozhikode
  { date: '2026-10-25', district: 'Kozhikode', market: 'Kozhikode Big Bazaar / Valiyangadi', crop: 'Coconut', variety: 'Dry Copra Rajapur', min_price: 11500, max_price: 12800, modal_price: 12200, price_unit: 'INR/quintal', price_verified: true, source: 'Valiyangadi Merchants Association', distance_km_from_district_center: 2 },
  { date: '2026-10-25', district: 'Kozhikode', market: 'Kozhikode Wholesale Market', crop: 'Banana', variety: 'Nendran', min_price: 4300, max_price: 5000, modal_price: 4700, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 3 },
  { date: '2026-10-25', district: 'Kozhikode', market: 'Perambra Mandi', crop: 'Turmeric', variety: 'Dry bulbs', min_price: 10200, max_price: 11800, modal_price: 11000, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 38 },

  // Thiruvananthapuram
  { date: '2026-10-25', district: 'Thiruvananthapuram', market: 'Chala Market (Trivandrum)', crop: 'Tapioca', variety: 'Red Stalk (Chuvappu)', min_price: 1950, max_price: 2400, modal_price: 2200, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 2 },
  { date: '2026-10-25', district: 'Thiruvananthapuram', market: 'Nedumangad Regulated Market', crop: 'Vegetables', variety: 'Daily Mandi Auction', min_price: 3100, max_price: 3900, modal_price: 3500, price_unit: 'INR/quintal', price_verified: true, source: 'VFPCK Nedumangad', distance_km_from_district_center: 18 },
  { date: '2026-10-25', district: 'Thiruvananthapuram', market: 'Chala Market', crop: 'Banana', variety: 'Nendran', min_price: 4400, max_price: 5100, modal_price: 4800, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 2 },

  // Kannur
  { date: '2026-10-25', district: 'Kannur', market: 'Kannur Municipal Mandi', crop: 'Coconut', variety: 'Raw Fresh', min_price: 3700, max_price: 4200, modal_price: 3950, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 2 },
  { date: '2026-10-25', district: 'Kannur', market: 'Taliparamba Wholesale Market', crop: 'Black pepper', variety: 'Malabar Non-garbled', min_price: 59500, max_price: 62800, modal_price: 61400, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 22 },

  // Kasaragod
  { date: '2026-10-25', district: 'Kasaragod', market: 'Kasaragod APMC Mandi', crop: 'Coconut', variety: 'Copra Milling', min_price: 9100, max_price: 9700, modal_price: 9400, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 3 },
  { date: '2026-10-25', district: 'Kasaragod', market: 'Kanhangad Market', crop: 'Rubber', variety: 'RSS-4', min_price: 18100, max_price: 18800, modal_price: 18450, price_unit: 'INR/quintal', price_verified: true, source: 'Rubber Board Extension', distance_km_from_district_center: 28 },

  // Malappuram
  { date: '2026-10-25', district: 'Malappuram', market: 'Manjeri Wholesale Market', crop: 'Banana', variety: 'Nendran', min_price: 4250, max_price: 4800, modal_price: 4500, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 14 },
  { date: '2026-10-25', district: 'Malappuram', market: 'Tirur Regulated Market', crop: 'Coconut', variety: 'Fresh Nut', min_price: 3600, max_price: 4100, modal_price: 3850, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 26 },

  // Pathanamthitta
  { date: '2026-10-25', district: 'Pathanamthitta', market: 'Adoor Agricultural Market', crop: 'Tapioca', variety: 'M-4', min_price: 1850, max_price: 2250, modal_price: 2050, price_unit: 'INR/quintal', price_verified: true, source: 'AGMARKNET / DMI Kerala', distance_km_from_district_center: 18 },
  { date: '2026-10-25', district: 'Pathanamthitta', market: 'Ranni Mandi', crop: 'Rubber', variety: 'RSS-4', min_price: 18300, max_price: 19100, modal_price: 18700, price_unit: 'INR/quintal', price_verified: true, source: 'Rubber Board Ranni', distance_km_from_district_center: 16 },
];

export const RECENT_MARKET_ARRIVALS: MarketArrivalRecord[] = [
  { date: '2026-10-24', district: 'Palakkad', market: 'Palakkad APMC Mandi', crop: 'Rice', variety: 'Matta', arrival_quantity: 48.5, arrival_unit: 'Tonnes', source: 'AGMARKNET Daily Bulletin' },
  { date: '2026-10-24', district: 'Palakkad', market: 'Chittur Regulated Market', crop: 'Groundnut', variety: 'Bold Pod', arrival_quantity: 22.0, arrival_unit: 'Tonnes', source: 'AGMARKNET Daily Bulletin' },
  { date: '2026-10-24', district: 'Ernakulam', market: 'Ernakulam Market', crop: 'Banana', variety: 'Nendran', arrival_quantity: 65.2, arrival_unit: 'Tonnes', source: 'VFPCK Daily Terminal Report' },
  { date: '2026-10-24', district: 'Ernakulam', market: 'Mattancherry Spice Exchange', crop: 'Black pepper', variety: 'Garbled MG-1', arrival_quantity: 14.8, arrival_unit: 'Tonnes', source: 'IPSTA Daily Report' },
  { date: '2026-10-24', district: 'Thrissur', market: 'Thrissur Central Market', crop: 'Rice', variety: 'Jyothi', arrival_quantity: 34.0, arrival_unit: 'Tonnes', source: 'AGMARKNET Daily Bulletin' },
  { date: '2026-10-24', district: 'Wayanad', market: 'Kalpetta Agri Market', crop: 'Ginger', variety: 'Green Ginger', arrival_quantity: 18.5, arrival_unit: 'Tonnes', source: 'Wayanad Mandi Arrivals' },
  { date: '2026-10-24', district: 'Kollam', market: 'Anchal Market', crop: 'Tapioca', variety: 'Edible fresh', arrival_quantity: 28.0, arrival_unit: 'Tonnes', source: 'AGMARKNET Daily Bulletin' },
  { date: '2026-10-24', district: 'Kottayam', market: 'Kottayam Rubber Market', crop: 'Rubber', variety: 'RSS-4', arrival_quantity: 92.4, arrival_unit: 'Tonnes', source: 'Rubber Board Trade Report' },
  { date: '2026-10-24', district: 'Kozhikode', market: 'Valiyangadi', crop: 'Coconut', variety: 'Dry Copra', arrival_quantity: 52.0, arrival_unit: 'Tonnes', source: 'Valiyangadi Merchants' },
  { date: '2026-10-24', district: 'Thiruvananthapuram', market: 'Chala Market', crop: 'Vegetables', variety: 'Mixed Daily', arrival_quantity: 41.5, arrival_unit: 'Tonnes', source: 'VFPCK Terminal Arrivals' },
];
