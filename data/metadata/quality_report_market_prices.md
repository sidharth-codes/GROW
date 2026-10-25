# Data Quality Report: Historical Agricultural Market Prices

- **Dataset Identifier:** `market_prices`
- **Generated At:** 2026-10-25 13:03:17
- **Status:** AWAITING USER UPLOAD

## Collection Status and Diagnostics

Automated ingestion from Data.gov.in requires a registered API key (`api-key`), and the official Agmarknet portal (agmarknet.gov.in) uses dynamic session state and CAPTCHAs which restrict headless unauthenticated bulk extraction.

To maintain scientific integrity without fabricating synthetic prices, GROW requires an authentic export from Agmarknet or an API key.

### Instructions to Provide Data:

1. Open [Agmarknet](https://agmarknet.gov.in/PriceTrends/SA_Pri_Month.aspx)
2. Filter: State = 'Kerala', select target crops, select date range
3. Export to CSV
4. Place the file in `data\raw\market_prices/` or upload via the GROW UI.
5. An official CSV template is available at: `data\raw\market_prices\market_prices_template.csv`
