# Data Quality Report: Historical Crop Yield and Production Statistics

- **Dataset Identifier:** `crop_yield`
- **Target File:** `data\processed\crop_yield.csv`
- **Generated At:** 2026-10-25 13:01:54
- **Overall Status:** PASS (Valid)

## Summary Metrics

| Metric | Value |
| :--- | :--- |
| Total Records | 6422 |
| Total Columns | 8 |
| Total Missing Values | 0 |
| Duplicate Records | 0 |
| Schema Compliance | 100% |

## Missing Values by Column

| Column | Missing Count | % Missing |
| :--- | :--- | :--- |
| `year` | 0 | 0.0% |
| `district` | 0 | 0.0% |
| `crop` | 0 | 0.0% |
| `season` | 0 | 0.0% |
| `area_hectares` | 0 | 0.0% |
| `production_tonnes` | 0 | 0.0% |
| `yield_kg_per_hectare` | 0 | 0.0% |
| `source` | 0 | 0.0% |

## Known Agricultural Data Limitations

- Yield figures represent district aggregated averages and may not reflect specific parcel yield variations.

## Agricultural Statistics Methodology

Statistics originate from the Department of Economics and Statistics (DES), Government of Kerala (Agricultural Statistics Portal dataset 28). The records reflect annual state agricultural censuses and crop-cutting experiments.

- **Observation Period:** 2001-02 to 2023-24
- **Total Districts:** 14 of 14 Kerala districts
- **Standardized Crops (22):** Rice (Paddy), Coconut, Banana, Black pepper, Rubber, Tapioca, Ginger, Turmeric, Arecanut, Cardamom, Cashew, Coffee, Tea, Plantain, etc.
- **Units:** Area (Hectares), Production (Metric Tonnes), Yield (Kg/Hectare).
- **Coconut Conversion:** Production reported in Million Nuts converted to equivalent metric tonnes (~1,200 MT per million nuts).
