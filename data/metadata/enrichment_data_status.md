# GROW data enrichment status

## Imported data and provenance

- The follow-up missing-data pack's 14 archive files (reference CSV, nine
  templates, source registry, and source notes) were extracted to new paths
  without overwriting existing files. Its reference CSV remains isolated under
  `data/reference/` and is not analysis-ready.
- The Cost A reference contains 350 rows across 35 crop/season labels and 10
  years (2014-15 through 2023-24). All 350 values were compared with table
  A5.1 in the downloaded official 2023-24 Kerala DES report; zero mismatches
  were found. The separate normalized dataset is schema-validated and remains
  statewide/reference-only, not a profitability input. Its 108 printed zeros
  are retained without interpreting them as measured zero costs. See
  `quality_report_kerala_statewide_cost_a_timeseries.md`.
- The nine follow-up templates are in `data/templates/missing_data_pack/` to
  keep them separate from earlier pack templates with different headers.
  They are header-only and are not observations.
- The follow-up source registry and source notes are preserved as
  `missing_data_pack_source_registry.json` and
  `missing_data_pack_source_notes.md`.
- The pack's 36 files under `existing_grow_data/` were compared with the
  corresponding project files by SHA-256; all matched. They were not copied
  over or otherwise replaced.
- The supplied
  `kerala_cost_of_cultivation_summary_2022_23_2023_24.csv` is retained verbatim
  under `data/raw/cultivation_cost/`, then schema-validated before copies were
  published to `data/` and `data/processed/`.
- The summary contains 70 statewide seasonal/annual rows for agricultural years
  2022-23 and 2023-24, with 11 columns. Its two missing numeric values are the
  unreported 2022-23 Beans/Summer cost and output value. Both remain blank.
- Both original reports were downloaded. All 34 numeric 2022-23 rows and all 35
  numeric 2023-24 rows were cross-checked in table order with zero mismatches;
  the two unreported 2022-23 Beans/Summer cells remain blank. See
  `kerala_cost_summary_verification.json` and
  `quality_report_cultivation_cost_summary.md`.

## Existing data availability

| Data | Available records | Coverage / interpretation |
|---|---:|---|
| Weather | 60,329 | Validated daily NASA POWER gridded estimates, 2015-01-01 through 2026-10-20 across 14 districts; not station measurements. 4,077 valid new records were merged and 25 rainfall outliers were quarantined verbatim. |
| Crop yield | 6,422 | Existing historical district/crop records; consult source and schema for units. |
| Qualitative soil profiles | 23 | Regional qualitative profiles, not farm soil-lab measurements. |
| Crop catalog | 10 | Existing crop guidance; not comprehensive verified requirements. |
| Soil/crop suitability | 230 | Existing rule-based heuristic scores, not probabilities or field-calibrated results. |
| Market prices | 0 | No authentic observations supplied; forecast remains unavailable. |
| Detailed cultivation costs | 0 | No district-level itemized cost records supplied. |
| Market arrivals/demand | 0 | Official AGMARKNET price/arrival report portal identified, but its page returned only a JavaScript shell and no verifiable record schema or downloadable dataset. No arrivals imported; demand is not inferred. |
| State-level cultivation-cost summary | 70 | 69 numeric rows verified against original Kerala DES 2022-23/2023-24 report tables; two cells remain blank for unreported Beans/Summer (2022-23). Statewide only. |
| Statewide Cost A time series | 350 | Kerala DES Cost A, 2014-15 through 2023-24; all values verified against official table A5.1, statewide only, not a profitability input. |

## Template-only areas

The five files in `data/templates/` contain headers only and are not
observations: market prices, market arrivals, soil measurements, crop calendar,
and expanded crop requirements. They must not be used for training or treated
as collected data.

The templates do not all match the current canonical schemas:

- The price template includes arrivals and source metadata beyond
  `market_prices.csv`; keep the canonical ingestion schema unchanged until a
  documented mapping is implemented.
- The arrivals template is mapped to the separate `market_arrivals.csv`
  dataset. Its required `arrival_unit` is preserved without conversion; the
  pack contains no authentic arrival observations.
- Arrivals are not treated as demand or merged into the older `demand.csv`
  schema.
- Soil measurements are not equivalent to the existing qualitative `soil.csv`.
- The crop calendar template and expanded crop requirements template require
  verified sources and schema mapping before ingestion.
- The statewide summary is not compatible with the district-level
  `cultivation_cost.csv` schema. It is registered and exposed as the separate
  `cultivation_cost_summary` dataset.

## Collection notes

The existing NASA POWER collector and AGMARKNET price pipeline are retained.
Weather promotion now requires all requested downloads and schema validation to
succeed; failed/invalid updates leave existing canonical files unchanged.
Authentic AGMARKNET arrival CSVs can be uploaded through the existing
schema-validated dataset upload flow as `market_arrivals`; the original unit,
source, retrieval time, and optional source record ID are retained.
The 2026 NASA POWER retrieval, endpoint, response metadata, units, missingness,
raw-file location, validation, and quarantine are recorded in
`weather_collection_attempt_2026-10-25.md`. The full-period/single-day response
discrepancies found for two anomalous dates are documented; no outlier was
altered or promoted.

AGMARKNET/data.gov.in's public resource page is accessible, but the project's
configured API request returned HTTP 400 with `Authorization field missing`.
No authenticated record response was available to verify the resource ID,
field schema, units, or date coverage, and no price or arrival rows were
imported. The configured resource ID in the existing fetcher is
`9ef84268-d588-465a-a308-a864a43d0070`; treat that as project configuration,
not as a resource ID confirmed by a successful download.

At this run, `DATA_GOV_IN_API_KEY` was absent from process, Windows user, and
machine environments. To configure access without exposing the key in chat,
set it as a Windows user environment variable (Settings > System > About >
Advanced system settings > Environment Variables), then restart VS Code. Do
not commit the key. An authenticated response is still needed to verify the
resource's actual schema and coverage before ingestion.

The National Portal of India links its “Prices & Arrival Reports, Agmarknet”
entry to `https://agmarknet.gov.in/pricearrivalreportlist`. The official
AGMARKNET route and candidate legacy arrival-report routes return an HTTP 200
JavaScript application shell (~1 KB) with no response records or schema. No
separate arrivals API/resource ID or downloadable data could be verified.

The KAU Package of Practices page and its chapter pages are publicly reachable,
but they are a publication rather than a machine-readable crop calendar or
requirements dataset; edition, crop/date/unit coverage, and extraction rights
for a structured export remain unresolved. No crop records were imported.
Kerala's official soil-survey portal links soil-association map PDFs for all
14 districts and has qualitative soil-class descriptions, but no structured
lab-measurement schema, units, sample/date coverage, or data-reuse terms were
verified. The separate soil-fertility portal returned HTTP 503. No measured
soil observations were added.

Profitability remains unavailable without matching district-level itemized
costs, authentic market-price observations, and aligned yield assumptions. The
state-level report summary is not substituted for any of those inputs.
