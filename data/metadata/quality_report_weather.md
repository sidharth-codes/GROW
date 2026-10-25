# Data Quality Report: Historical Meteorological Observations

- **Dataset Identifier:** `weather`
- **Target File:** `data\processed\weather.csv`
- **Generated At:** 2026-10-25 18:26:24
- **Overall Status:** PASS (Valid)

## Summary Metrics

| Metric | Value |
| :--- | :--- |
| Total Records | 60329 |
| Total Columns | 9 |
| Total Missing Values | 0 |
| Duplicate Records | 0 |
| Schema Compliance | 100% |

## Missing Values by Column

| Column | Missing Count | % Missing |
| :--- | :--- | :--- |
| `district` | 0 | 0.0% |
| `date` | 0 | 0.0% |
| `rainfall_mm` | 0 | 0.0% |
| `temperature_min_c` | 0 | 0.0% |
| `temperature_max_c` | 0 | 0.0% |
| `humidity_percent` | 0 | 0.0% |
| `latitude` | 0 | 0.0% |
| `longitude` | 0 | 0.0% |
| `source` | 0 | 0.0% |

## Known Agricultural Data Limitations

- Gridded satellite-reanalysis estimates (~0.5 deg resolution); not direct ground weather-station observations.

## Geographical Coverage and Methodology

Observations are derived from NASA POWER's Agroclimatology (AG) daily archive, based on Modern-Era Retrospective Analysis for Research and Applications (MERRA-2) and Goddard Earth Observing System (GEOS) satellite-reanalysis models (~0.5° resolution).

**Representative Coordinates:**

| District | Latitude | Longitude | Elevation | Region |
| :--- | :--- | :--- | :--- | :--- |
| Thiruvananthapuram | 8.5241°N | 76.9366°E | 16 m | South Kerala Coastal/Midland |
| Kollam | 8.8932°N | 76.6141°E | 15 m | South Kerala Coastal/Midland |
| Pathanamthitta | 9.2648°N | 76.7870°E | 19 m | Central Travancore Foothills |
| Alappuzha | 9.4981°N | 76.3388°E | 1 m | Kuttanad Lowlands |
| Kottayam | 9.5916°N | 76.5222°E | 12 m | Central Midlands |
| Idukki | 9.8494°N | 76.9710°E | 750 m | High Ranges (Western Ghats) |
| Ernakulam | 9.9816°N | 76.2999°E | 4 m | Central Coastal & Alluvial Plains |
| Thrissur | 10.5276°N | 76.2144°E | 2.8 m | Central Lowlands & Kole Lands |
| Palakkad | 10.7867°N | 76.6548°E | 84 m | Palakkad Gap Agrarian Basin |
| Malappuram | 11.0735°N | 76.0740°E | 28 m | North-Central Midland |
| Kozhikode | 11.2588°N | 75.7804°E | 1 m | North Malabar Coast |
| Wayanad | 11.6103°N | 76.0827°E | 780 m | Wayanad Plateau (Western Ghats) |
| Kannur | 11.8745°N | 75.3704°E | 16 m | North Malabar |
| Kasaragod | 12.5102°N | 74.9852°E | 19 m | Northernmost Coastal & Laterite Plateau |

> [!NOTE]
> Gridded satellite-reanalysis estimates represent spatial cell averages (~50 km grid box) and may not match point observations from IMD surface weather stations or extreme micro-climatic rain shadows.

## Latest Collection

- **Retrieved at:** 2026-10-25T18:26:24+05:30
- **Requested period:** 2026-01-01 to 2026-10-20
- **New source records parsed:** 4,102
- **New source records within rainfall schema bounds:** 4,077
- **Rainfall records quarantined by validation:** 25
- **Districts retrieved:** 14
- **Rows in validated merged dataset:** 60,329
- **Merged observation period:** 2015-01-01 to 2026-10-20
- **Missing values by column in merged dataset:** {"date": 0, "district": 0, "humidity_percent": 0, "latitude": 0, "longitude": 0, "rainfall_mm": 0, "source": 0, "temperature_max_c": 0, "temperature_min_c": 0}
- **Raw response cache:** `data/raw/weather/`
- **NASA POWER time standard:** provider default local solar time (LST).
- **Requested parameters and canonical units:** PRECTOTCORR (mm/day), T2M_MIN (deg C), T2M_MAX (deg C), RH2M (%).
- **Provider time standard reported:** LST.
- **NASA POWER API version:** v2.10.1.
- **Provider PRECTOTCORR descriptor:** Precipitation Corrected.
- **Provider response units:** PRECTOTCORR `mm/day`; T2M_MIN/T2M_MAX `C`; RH2M `%`.
- **Quarantine details:** `metadata/weather_validation_anomalies_20260101_20261020_20261025182620.csv`; raw provider responses remain unchanged.

| District | New records | Source | Missing PRECTOTCORR | Missing T2M_MIN | Missing T2M_MAX | Missing RH2M |
|---|---:|---|---:|---:|---:|---:|
| Thiruvananthapuram | 293 | local_raw_cache | 0 | 0 | 0 | 0 |
| Kollam | 293 | local_raw_cache | 0 | 0 | 0 | 0 |
| Pathanamthitta | 293 | local_raw_cache | 0 | 0 | 0 | 0 |
| Alappuzha | 293 | local_raw_cache | 0 | 0 | 0 | 0 |
| Kottayam | 293 | local_raw_cache | 0 | 0 | 0 | 0 |
| Idukki | 293 | local_raw_cache | 0 | 0 | 0 | 0 |
| Ernakulam | 293 | local_raw_cache | 0 | 0 | 0 | 0 |
| Thrissur | 293 | local_raw_cache | 0 | 0 | 0 | 0 |
| Palakkad | 293 | local_raw_cache | 0 | 0 | 0 | 0 |
| Malappuram | 293 | local_raw_cache | 0 | 0 | 0 | 0 |
| Kozhikode | 293 | local_raw_cache | 0 | 0 | 0 | 0 |
| Wayanad | 293 | local_raw_cache | 0 | 0 | 0 | 0 |
| Kannur | 293 | local_raw_cache | 0 | 0 | 0 | 0 |
| Kasaragod | 293 | local_raw_cache | 0 | 0 | 0 | 0 |

### Quarantined precipitation values

| District | Date | Value | Unit | Reason |
|---|---|---:|---|---|
| Thiruvananthapuram | 2026-07-31 | 1154.4 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Thiruvananthapuram | 2026-08-07 | 1431.6 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Kollam | 2026-07-31 | 1066.08 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Alappuzha | 2026-07-31 | 1269.36 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Alappuzha | 2026-08-01 | 1418.64 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Alappuzha | 2026-08-03 | 1517.52 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Kottayam | 2026-07-31 | 1269.36 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Kottayam | 2026-08-01 | 1418.64 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Kottayam | 2026-08-03 | 1517.52 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Ernakulam | 2026-07-31 | 1196.16 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Ernakulam | 2026-08-01 | 1475.76 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Ernakulam | 2026-08-03 | 1164.96 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Thrissur | 2026-08-01 | 1275.36 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Malappuram | 2026-10-16 | 1167.36 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Kozhikode | 2026-08-01 | 1140.24 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Kozhikode | 2026-10-16 | 1101.84 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Wayanad | 2026-10-15 | 1150.56 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Wayanad | 2026-10-16 | 1923.84 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Kannur | 2026-08-01 | 1159.92 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Kannur | 2026-10-16 | 1236.96 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Kasaragod | 2026-05-23 | 1101.12 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Kasaragod | 2026-06-30 | 1417.68 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Kasaragod | 2026-07-19 | 1047.12 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Kasaragod | 2026-07-20 | 1319.76 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |
| Kasaragod | 2026-08-01 | 1376.16 | mm/day | Rainfall exceeds schema maximum 1000.0 mm. |

### Provider response rechecks

The original full-period JSON and separate provider rechecks are preserved in
`data/raw/weather/` and `data/raw/weather/validation_rechecks/`. They contain
the same `mm/day` parameter metadata, but request-window comparisons were not
consistent for every date:

| District/date | Full-period result (mm/day) | Single-day result (mm/day) |
|---|---:|---:|
| Alappuzha, 2026-08-03 | 1517.52 | 63.23 |
| Kasaragod, 2026-06-30 | 1417.68 | 59.07 |
| Wayanad, 2026-10-16 | 1923.84 | 1923.84 |

The first two pairs differ by a factor of 24; the Wayanad outlier reproduced.
This demonstrates that the anomalous full-period responses cannot safely be
corrected by applying a guessed conversion. Values above the existing
1,000 mm/day schema bound were quarantined verbatim and excluded from the
canonical CSV. The 4,077 other records passed the current schema and were
promoted; no anomalous value was clamped or converted.
