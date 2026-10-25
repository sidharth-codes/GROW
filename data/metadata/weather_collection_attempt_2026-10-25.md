# NASA POWER collection: 2026-10-25

## Source and response

- **Endpoint:** `https://power.larc.nasa.gov/api/temporal/daily/point`
- **Access:** Public API; all 14 district responses returned HTTP 200.
- **Requested period:** 2026-01-01 through 2026-10-20
- **Response shape:** Daily series under `properties.parameter`, with provider
  units under `parameters` and query/source metadata under `header`.
- **Provider metadata:** NASA POWER Daily API v2.10.1; sources MERRA2, GEOSIT,
  POWER; time standard LST.
- **Requested parameters/units:** PRECTOTCORR `mm/day`; T2M_MIN and T2M_MAX
  `C`; RH2M `%`.
- **Raw payloads:** 14 district responses, each with 293 dates, in
  `data/raw/weather/`. Independent full-window/single-day rechecks are under
  `data/raw/weather/validation_rechecks/`.

## Validation and promotion

- **Districts retrieved:** 14 of 14
- **Parsed records:** 4,102 (293 per district)
- **Provider missing sentinels:** 0 for each requested parameter.
- **Rainfall values within the canonical schema bounds:** 4,077
- **Rainfall values quarantined:** 25, across 11 districts and 10 dates.
- **Quarantine threshold:** Existing `weather.rainfall_mm` schema maximum,
  1,000 mm per day. The source values were preserved verbatim with district,
  date, unit, reason, and raw response path in
  `data/metadata/weather_validation_anomalies_20260101_20261020_20261025182620.csv`.
- **Promotion:** 4,077 new records were added after merged-file validation;
  the 56,252 existing valid rows were retained. The canonical dataset now has
  60,329 rows, zero missing cells, zero duplicate keys, and passes validation.
- **Final coverage:** 2015-01-01 through 2026-10-20; all 14 Kerala districts.

## Anomaly investigation

The JSON metadata labels PRECTOTCORR `mm/day`; the parser now preserves raw
rainfall and humidity values instead of clamping them. The 25 out-of-bound
values were not converted or inserted into the canonical CSV.

Request-window rechecks found inconsistent NASA POWER values for two
district/date pairs, while a third outlier reproduced:

| District/date | Full-period value | Single-day value | Unit |
|---|---:|---:|---|
| Alappuzha, 2026-08-03 | 1517.52 | 63.23 | mm/day |
| Kasaragod, 2026-06-30 | 1417.68 | 59.07 | mm/day |
| Wayanad, 2026-10-16 | 1923.84 | 1923.84 | mm/day |

The first two values differ by a factor of 24. There is no defensible basis to
choose a conversion or substitute the single-day result for the original
full-period observation, so the original out-of-bound records remain
quarantined. See `data/metadata/quality_report_weather.md` for the complete
quarantine table and missing-value counts.

## Source references

- [NASA POWER Daily API documentation](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)
- [NASA POWER API](https://power.larc.nasa.gov/api/temporal/daily/point)
