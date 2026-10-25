# Data Quality Report: Historical Meteorological Observations

- **Dataset Identifier:** `weather`
- **Target File:** `data\processed\weather.csv`
- **Generated At:** 2026-10-25 12:55:16
- **Overall Status:** PASS (Valid)

## Summary Metrics

| Metric | Value |
| :--- | :--- |
| Total Records | 56252 |
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
