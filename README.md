# GROW — Kerala Agricultural Intelligence and Decision Support

GROW is a data-driven agricultural intelligence platform focused on Kerala, India. It assists farmers, extension officers, and agricultural planners in exploring crop suitability, soil characteristics, weather history, reported crop yield, wholesale market prices, and authentic dataset management.

## Architecture

This project is built as a modern **React SPA on Vite**:

- **Framework**: React 18, TypeScript, Vite
- **Data Engine**: Client-side TypeScript analytics service backed by authentic Kerala datasets and schema validation
- **Styling**: Tailored design system preserving the GROW aesthetic with Manrope & DM Sans typography, green accents, metric cards, and responsive sidebar navigation
- **Port**: Runs on port 3000 (host `0.0.0.0`)

## Features & Workspaces

1. **Overview**: Live field overview showing data coverage, active dataset metrics, compatibility snapshots, and documented limitations.
2. **Crop Recommendations**: Equal-weight soil texture, drainage, and estimated pH compatibility heuristic ranking across Kerala districts and soil profiles.
3. **Soil Analysis**: Qualitative district-level soil orders, textures, and KMeans indicative clustering reference.
4. **Weather History**: Daily historical NASA POWER meteorological records (rainfall, min/max temperature, relative humidity) with interactive SVG trend visualization and 30-day summaries.
5. **Yield**: Observed annual district crop yield statistics (DES Kerala) and training baseline mean references.
6. **Market Prices**: Wholesale Agmarknet market observations, price unit verification notices, and deferred forecasting thresholds.
7. **Profitability**: Authentic gross margin calculations when real cost and price inputs match, with explicit notices when data are unavailable.
8. **Datasets**: Dataset management inventory, source download guidance for official portals, and in-browser CSV schema validation with intake reporting.
9. **Model Performance**: Saved evaluation artifacts for soil clustering, crop yield prediction, and market price forecasting.

## Getting Started

```bash
# Install dependencies
npm install

# Start the development server
npm run dev

# Build for production
npm run build
```

Open `http://localhost:3000` to interact with the GROW platform.
