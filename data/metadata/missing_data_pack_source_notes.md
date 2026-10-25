# GROW Missing Data Pack

## What this pack contains
- CSV templates for market prices, market arrivals, detailed cultivation costs, crop calendar, soil laboratory measurements, crop requirements, demand, weather forecasts, and crop risk.
- A statewide Kerala DES Cost A time-series reference CSV transcribed from the 2023–24 report's cropwise historical comparison table.
- Source registry, downloader scaffolds, and an integration prompt.

## What it does not contain
This is not a full data dump. No live external API requests were completed while preparing this pack. No authentic market-price or market-arrival records, district-specific costs, soil lab measurements, consumer-demand observations, or validated crop calendar records are bundled. The templates are header-only.

## Caution about the Cost A reference file
The time-series values were transcribed from the official Kerala DES report's table titled cropwise time-series comparison of Cost A, 2014–15 through 2023–24. Before using it in production:
1. Compare every value with the original report.
2. Confirm units (the table describes Cost A per hectare).
3. Treat zero values cautiously: they may represent crops/years not covered or not reported, not a true zero cost.
4. Do not substitute Cost A for Cost C or total farmer cost. The report defines multiple cost concepts.
5. Keep the data reference-only until verified.

## Official sources
- Kerala DES Cost of Cultivation report 2023–24: https://ecostat.kerala.gov.in/publication-detail/report-on-cost-of-cultivation-of-important-crops-in-kerala-2023-24
- Kerala DES dataset listing: https://ecostat.kerala.gov.in/dataset/66
- Kerala DES district-wise crop statistics: https://ecostat.kerala.gov.in/dataset/28
- AGMARKNET / data.gov.in daily market prices: https://data.gov.in/resource/variety-wise-daily-market-prices-data-commodity
- data.gov.in API portal: https://api.data.gov.in/
- NASA POWER Daily API docs: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
- Kerala Agricultural University Package of Practices: https://kau.in/book/package-practices-recommendations-crops
- Kerala Soil Fertility Information System: https://www.keralasoilfertility.net/

## Downloader scripts
`download_agmarknet_data.py` requires the official resource ID and `DATA_GOV_IN_API_KEY`. It refuses to write an empty dataset.
`download_nasa_power_daily.py` retrieves daily NASA POWER data for a specified point. Verify units and missing-value sentinels before integrating.

## Integration
Give `AGENT_INTEGRATION_PROMPT.txt` to your coding agent along with this ZIP and your current GROW repository. Do not let it overwrite original datasets without review.
