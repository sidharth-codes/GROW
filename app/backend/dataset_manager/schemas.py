"""Schema definitions and metadata specifications for GROW datasets.

Includes definitions for all 9 agricultural domains covering Kerala:
1. Soil characteristics
2. Crop requirements
3. Historical weather
4. Crop yield and production
5. Historical market prices
6. Cultivation costs
7. Market arrivals and demand
8. Crop calendar and risks
9. Soil-crop suitability heuristics
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any


KERALA_DISTRICTS = [
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
]


@dataclass
class ColumnDef:
    name: str
    dtype: str  # 'string', 'float', 'integer', 'date' (YYYY-MM-DD), 'range'
    required: bool = True
    description: str = ""
    unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[str]] = None


@dataclass
class ValidationIssue:
    level: str  # 'ERROR', 'WARNING', 'INFO'
    row: Optional[int]
    column: Optional[str]
    message: str


@dataclass
class ValidationResult:
    is_valid: bool
    record_count: int
    column_count: int
    missing_value_count: int
    missing_values_by_column: Dict[str, int]
    duplicate_record_count: int
    errors: List[str]
    warnings: List[str]
    details: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DatasetSourceInfo:
    organization: str
    source_url: str
    download_method: str  # 'api', 'direct_download', 'manual_export', 'manual_upload'
    api_endpoint: Optional[str] = None
    manual_page_url: Optional[str] = None
    manual_export_instructions: Optional[str] = None
    expected_filename: str = ""
    expected_format: str = "CSV"
    license_or_terms: str = "Open Government Data (OGD) India / Public Educational"


@dataclass
class DatasetMeta:
    dataset_id: str
    name: str
    category: str
    description: str
    status: str  # 'ready_for_analysis', 'partially_available', 'not_collected', 'awaiting_upload', 'validation_failed'
    source_info: DatasetSourceInfo
    geographic_coverage: str = "Kerala, India"
    geographic_resolution: str = "District"
    observation_period: str = "Not recorded"
    record_count: int = 0
    column_count: int = 0
    last_updated: Optional[str] = None
    raw_path: Optional[str] = None
    processed_path: Optional[str] = None
    validation_status: Optional[str] = None
    data_quality_limitations: List[str] = field(default_factory=list)
    processing_steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return data


DATASET_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "crops": {
        "dataset_id": "crops",
        "name": "Crop Agronomic Requirements",
        "category": "Crop requirements",
        "description": "Baseline agronomic requirements for 10 prominent Kerala crops.",
        "primary_key": ["crop"],
        "columns": [
            ColumnDef("crop", "string", required=True, description="Crop name"),
            ColumnDef("preferred_soil_texture", "string", required=True, description="Optimal soil texture classes"),
            ColumnDef("preferred_drainage", "string", required=True, description="Required drainage condition"),
            ColumnDef("preferred_ph_range", "range", required=True, description="Optimal pH range min-max"),
            ColumnDef("water_requirement", "string", required=True, allowed_values=["Low", "Medium", "High"], description="Water requirement intensity"),
            ColumnDef("growing_season", "string", required=True, description="Primary cultivation season in Kerala"),
        ],
        "source_info": DatasetSourceInfo(
            organization="Kerala Agricultural University (KAU)",
            source_url="https://kau.in/",
            download_method="manual_upload",
            manual_page_url="https://celkau.in/tech_agri/package_of_practices.aspx",
            manual_export_instructions="Refer to KAU Package of Practices for Crops. Verify crops, textures, drainage, and pH bounds.",
            expected_filename="crops.csv",
        ),
        "limitations": [
            "Covers 10 major crops; micro-climatic variety variations within crops are not yet disaggregated.",
            "pH ranges represent general agronomic guidelines rather than crop-variety-specific tolerances.",
        ],
    },
    "soil": {
        "dataset_id": "soil",
        "name": "Kerala District Soil Profile",
        "category": "Soil characteristics",
        "description": "Representative soil orders, textures, and qualitative fertility classes across Kerala districts.",
        "primary_key": ["district", "soil_type"],
        "columns": [
            ColumnDef("district", "string", required=True, description="Kerala district name", allowed_values=KERALA_DISTRICTS),
            ColumnDef("soil_type", "string", required=True, description="Soil classification / local type"),
            ColumnDef("soil_texture", "string", required=True, description="Soil texture category"),
            ColumnDef("drainage", "string", required=True, description="Drainage profile"),
            ColumnDef("soil_depth", "string", required=True, description="Effective soil depth class"),
            ColumnDef("ph_category", "string", required=True, description="Qualitative pH status (e.g. Strongly acidic, Near neutral)"),
            ColumnDef("organic_matter_category", "string", required=True, description="Qualitative organic matter class"),
            ColumnDef("fertility_category", "string", required=True, description="Qualitative natural fertility status"),
        ],
        "source_info": DatasetSourceInfo(
            organization="Department of Soil Survey & Soil Conservation, Govt. of Kerala",
            source_url="https://www.keralasoils.gov.in/",
            download_method="manual_upload",
            manual_page_url="https://www.keralasoilfertility.net/",
            manual_export_instructions="Visit Kerala Soil Fertility portal or Kerala Soil Survey report, export soil series/district profiles.",
            expected_filename="soil.csv",
        ),
        "limitations": [
            "Contains qualitative pH and fertility categories rather than quantitative laboratory test figures.",
            "District coverage currently has 13 of 14 districts (Pathanamthitta district is absent in initial dataset).",
            "Values reflect regional soil series benchmarks, not farm-specific spot soil samples.",
        ],
    },
    "soil_crop_suitability_v2": {
        "dataset_id": "soil_crop_suitability_v2",
        "name": "Soil-Crop Compatibility Matrix (Heuristic v2)",
        "category": "Crop risk and suitability constraints",
        "description": "Rule-based compatibility scoring combining soil texture, drainage, and estimated pH compatibility.",
        "primary_key": ["district", "soil_type", "crop"],
        "columns": [
            ColumnDef("district", "string", required=True, description="Kerala district"),
            ColumnDef("soil_type", "string", required=True, description="Soil type name"),
            ColumnDef("crop", "string", required=True, description="Target crop"),
            ColumnDef("texture_score", "float", required=True, min_value=0.0, max_value=100.0, unit="score"),
            ColumnDef("drainage_score", "float", required=True, min_value=0.0, max_value=100.0, unit="score"),
            ColumnDef("estimated_ph_score", "float", required=False, min_value=0.0, max_value=100.0, unit="score"),
            ColumnDef("suitability_score", "float", required=True, min_value=0.0, max_value=100.0, unit="score"),
            ColumnDef("ph_status", "string", required=True, description="Explanation of qualitative pH estimation"),
            ColumnDef("score_method", "string", required=True, description="Heuristic algorithm description"),
        ],
        "source_info": DatasetSourceInfo(
            organization="GROW Internal Agronomic Heuristics",
            source_url="internal://heuristic_v2",
            download_method="manual_upload",
            expected_filename="soil_crop_suitability_v2.csv",
        ),
        "limitations": [
            "Scores are derived from rule-based heuristic formulas, NOT statistically trained or field-calibrated ML models.",
            "Estimated pH scores rely on midpoint mappings of qualitative descriptions.",
        ],
    },
    "weather": {
        "dataset_id": "weather",
        "name": "Historical Meteorological Observations",
        "category": "Historical weather",
        "description": "Daily rainfall, temperature min/max, and relative humidity for Kerala districts.",
        "primary_key": ["district", "date"],
        "columns": [
            ColumnDef("district", "string", required=True, description="District name", allowed_values=KERALA_DISTRICTS),
            ColumnDef("date", "date", required=True, description="Date in YYYY-MM-DD format"),
            ColumnDef("rainfall_mm", "float", required=True, min_value=0.0, max_value=1000.0, unit="mm"),
            ColumnDef("temperature_min_c", "float", required=True, min_value=0.0, max_value=45.0, unit="celsius"),
            ColumnDef("temperature_max_c", "float", required=True, min_value=10.0, max_value=55.0, unit="celsius"),
            ColumnDef("humidity_percent", "float", required=True, min_value=0.0, max_value=100.0, unit="percent"),
            ColumnDef("latitude", "float", required=True, min_value=8.0, max_value=13.0, unit="degrees_north"),
            ColumnDef("longitude", "float", required=True, min_value=74.0, max_value=78.0, unit="degrees_east"),
            ColumnDef("source", "string", required=False, description="Data source indicator"),
        ],
        "source_info": DatasetSourceInfo(
            organization="NASA Prediction Of Worldwide Energy Resources (POWER)",
            source_url="https://power.larc.nasa.gov/",
            download_method="api",
            api_endpoint="https://power.larc.nasa.gov/api/temporal/daily/point",
            manual_page_url="https://power.larc.nasa.gov/data-access-viewer/",
            manual_export_instructions="Open NASA POWER Data Access Viewer, choose Meteorology/Agroclimatology, select Kerala centroid coordinates, date range 2015-01-01 to 2025-12-31, parameters PRECTOTCORR, T2M_MIN, T2M_MAX, RH2M, format CSV.",
            expected_filename="weather.csv",
        ),
        "limitations": [
            "Gridded satellite-reanalysis estimates (~0.5 deg resolution); not direct ground weather-station observations.",
        ],
    },
    "crop_yield": {
        "dataset_id": "crop_yield",
        "name": "Historical Crop Yield and Production Statistics",
        "category": "Crop yield and production",
        "description": "Historical crop area, production, and productivity across Kerala districts.",
        "primary_key": ["year", "district", "crop", "season"],
        "columns": [
            ColumnDef("year", "string", required=True, description="Agricultural year (e.g. 2018-19 or 2018)"),
            ColumnDef("district", "string", required=True, description="District name", allowed_values=KERALA_DISTRICTS),
            ColumnDef("crop", "string", required=True, description="Crop name"),
            ColumnDef("season", "string", required=True, description="Cultivation season (Autumn/Kharif, Winter/Rabi, Summer, Annual)"),
            ColumnDef("area_hectares", "float", required=True, min_value=0.0, unit="hectares"),
            ColumnDef("production_tonnes", "float", required=True, min_value=0.0, unit="tonnes"),
            ColumnDef("yield_kg_per_hectare", "float", required=True, min_value=0.0, unit="kg/ha"),
            ColumnDef("source", "string", required=False, description="Source publication or portal"),
        ],
        "source_info": DatasetSourceInfo(
            organization="Department of Economics and Statistics (DES), Govt. of Kerala",
            source_url="https://ecostat.kerala.gov.in/",
            download_method="manual_upload",
            manual_page_url="https://ecostat.kerala.gov.in/dataset/28",
            manual_export_instructions="Visit DES Kerala Agricultural Statistics or data.desagri.gov.in, navigate to District-wise Crop Area & Production Reports, export CSV.",
            expected_filename="crop_yield.csv",
        ),
        "limitations": [
            "Yield figures represent district aggregated averages and may not reflect specific parcel yield variations.",
        ],
    },
    "market_prices": {
        "dataset_id": "market_prices",
        "name": "Historical Agricultural Market Prices",
        "category": "Historical market prices",
        "description": "Daily or monthly minimum, maximum, and modal wholesale prices in APMC/regulated markets in Kerala.",
        "primary_key": ["date", "district", "market", "crop"],
        "columns": [
            ColumnDef("date", "date", required=True, description="Trading date (YYYY-MM-DD)"),
            ColumnDef("district", "string", required=True, description="District name", allowed_values=KERALA_DISTRICTS),
            ColumnDef("market", "string", required=True, description="Market center name"),
            ColumnDef("crop", "string", required=True, description="Commodity name"),
            ColumnDef("variety", "string", required=False, description="Commodity variety"),
            ColumnDef("min_price", "float", required=True, min_value=0.0, unit="INR/quintal"),
            ColumnDef("max_price", "float", required=True, min_value=0.0, unit="INR/quintal"),
            ColumnDef("modal_price", "float", required=True, min_value=0.0, unit="INR/quintal"),
            ColumnDef("price_unit", "string", required=True, description="Currency and weight basis, e.g. INR/quintal"),
            ColumnDef("source", "string", required=False, description="Reporting agency / portal"),
        ],
        "source_info": DatasetSourceInfo(
            organization="Directorate of Marketing & Inspection (DMI) / Agmarknet / OGD India",
            source_url="https://agmarknet.gov.in/",
            download_method="manual_upload",
            manual_page_url="https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi",
            manual_export_instructions="Visit Agmarknet or data.gov.in, filter State='Kerala', select target crops, select historical range, export CSV.",
            expected_filename="market_prices.csv",
        ),
        "limitations": [
            "Wholesale APMC terminal market prices; farm-gate prices received by smallholders may be discounted by intermediary margins.",
        ],
    },
    "cultivation_cost": {
        "dataset_id": "cultivation_cost",
        "name": "Crop Cultivation Cost Structure",
        "category": "Cultivation costs",
        "description": "Itemized input and operational expenditures per hectare for Kerala crops.",
        "primary_key": ["district", "crop", "year"],
        "columns": [
            ColumnDef("district", "string", required=True, description="District name"),
            ColumnDef("crop", "string", required=True, description="Crop name"),
            ColumnDef("year", "string", required=True, description="Reference financial/crop year"),
            ColumnDef("land_preparation", "float", required=True, min_value=0.0, unit="INR/hectare"),
            ColumnDef("seeds_planting_material", "float", required=True, min_value=0.0, unit="INR/hectare"),
            ColumnDef("fertilizers", "float", required=True, min_value=0.0, unit="INR/hectare"),
            ColumnDef("labour", "float", required=True, min_value=0.0, unit="INR/hectare"),
            ColumnDef("irrigation", "float", required=True, min_value=0.0, unit="INR/hectare"),
            ColumnDef("pest_management", "float", required=True, min_value=0.0, unit="INR/hectare"),
            ColumnDef("harvesting", "float", required=True, min_value=0.0, unit="INR/hectare"),
            ColumnDef("transport", "float", required=True, min_value=0.0, unit="INR/hectare"),
            ColumnDef("other_costs", "float", required=True, min_value=0.0, unit="INR/hectare"),
            ColumnDef("total_cost_per_hectare", "float", required=True, min_value=0.0, unit="INR/hectare"),
            ColumnDef("source", "string", required=False, description="Survey source or cost report reference"),
        ],
        "source_info": DatasetSourceInfo(
            organization="Farm Management Studies / DES Kerala / CACP",
            source_url="https://ecostat.kerala.gov.in/",
            download_method="manual_upload",
            manual_page_url="https://cacp.da.gov.in/",
            manual_export_instructions="Consult DES Kerala 'Report on Cost of Cultivation of Important Crops in Kerala' or CACP State Tables. Extract cost components per hectare.",
            expected_filename="cultivation_cost.csv",
        ),
        "limitations": [
            "Costs are state or agro-zone survey benchmarks and will vary with farmer mechanization and local labor wages.",
        ],
    },
    "demand": {
        "dataset_id": "demand",
        "name": "Market Arrivals and Demand Indicators",
        "category": "Market arrivals and demand indicators",
        "description": "Physical commodity quantities arriving in major Kerala wholesale mandis.",
        "primary_key": ["date", "district", "market", "crop"],
        "columns": [
            ColumnDef("date", "date", required=True, description="Arrival date (YYYY-MM-DD)"),
            ColumnDef("district", "string", required=True, description="District name"),
            ColumnDef("market", "string", required=True, description="Market name"),
            ColumnDef("crop", "string", required=True, description="Crop name"),
            ColumnDef("arrivals_tonnes", "float", required=True, min_value=0.0, unit="tonnes"),
            ColumnDef("modal_price", "float", required=False, min_value=0.0, unit="INR/quintal"),
            ColumnDef("source", "string", required=False, description="Market reporting source"),
        ],
        "source_info": DatasetSourceInfo(
            organization="Agmarknet / Department of Agriculture & Farmers Welfare",
            source_url="https://agmarknet.gov.in/",
            download_method="manual_upload",
            manual_page_url="https://agmarknet.gov.in/PriceTrends/SA_Pri_Month.aspx",
            manual_export_instructions="Query Agmarknet arrival bulletins by commodity and Kerala markets, export arrivals CSV.",
            expected_filename="demand.csv",
        ),
        "limitations": [
            "Covers formal regulated markets only; informal farm-gate and local village trade volumes are unrecorded.",
        ],
    },
    "crop_calendar": {
        "dataset_id": "crop_calendar",
        "name": "Kerala Agricultural Calendar and Constraints",
        "category": "Planting and harvesting calendar",
        "description": "Agronomic window for sowing, peak growth, and harvest across seasons.",
        "primary_key": ["district", "crop", "season"],
        "columns": [
            ColumnDef("district", "string", required=True, description="District name"),
            ColumnDef("crop", "string", required=True, description="Crop name"),
            ColumnDef("season", "string", required=True, description="Season name (Kharif/Virippu, Rabi/Mundakan, Summer/Puncha)"),
            ColumnDef("sowing_start_month", "integer", required=True, min_value=1, max_value=12, description="Month 1-12"),
            ColumnDef("sowing_end_month", "integer", required=True, min_value=1, max_value=12, description="Month 1-12"),
            ColumnDef("harvest_start_month", "integer", required=True, min_value=1, max_value=12, description="Month 1-12"),
            ColumnDef("harvest_end_month", "integer", required=True, min_value=1, max_value=12, description="Month 1-12"),
            ColumnDef("duration_days", "integer", required=True, min_value=10, max_value=3650, description="Crop duration"),
            ColumnDef("source", "string", required=False, description="KAU / ICAR reference"),
        ],
        "source_info": DatasetSourceInfo(
            organization="Kerala Agricultural University (KAU) / ICAR",
            source_url="https://kau.in/",
            download_method="manual_upload",
            manual_page_url="https://celkau.in/",
            manual_export_instructions="Compile crop calendar from KAU Farm Guide or Package of Practices.",
            expected_filename="crop_calendar.csv",
        ),
        "limitations": [
            "Rainfed cropping schedules fluctuate depending on the exact onset of the South-West and North-East monsoons.",
        ],
    },
}
