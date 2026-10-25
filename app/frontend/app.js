const content = document.querySelector("#page-content");
const pageName = document.querySelector("#page-name");
const navigation = document.querySelector("#navigation");
const sidebar = document.querySelector("#sidebar");
const pageLabels = {
  dashboard: "Overview",
  recommendations: "Crop recommendations",
  soil: "Soil analysis",
  weather: "Weather history",
  yield: "Yield",
  market: "Market prices",
  profitability: "Profitability",
  datasets: "Datasets",
  models: "Model performance",
};
const state = { page: "dashboard", districts: [], crops: [], datasets: [], dashboard: null };

const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
}[char]));
const fmt = (value, digits = 0) => value == null || !Number.isFinite(Number(value))
  ? "—"
  : Number(value).toLocaleString("en-IN", { maximumFractionDigits: digits });
const query = (values) => new URLSearchParams(
  Object.entries(values).filter(([, value]) => value !== "" && value != null),
).toString();

async function api(path, options) {
  const response = await fetch(path, options);
  const result = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(result.error || result.message || `Request failed (${response.status})`);
  return result;
}

function heading(title, description, eyebrow = "GROW DATA INTELLIGENCE") {
  return `<div class="page-heading"><div><div class="eyebrow">${esc(eyebrow)}</div><h1>${esc(title)}</h1><p class="subtitle">${esc(description)}</p></div></div>`;
}
function panel(title, subtitle, body, tag = "") {
  return `<section class="surface panel"><div class="panel-head"><div><h2>${esc(title)}</h2>${subtitle ? `<p>${esc(subtitle)}</p>` : ""}</div>${tag ? `<span class="tag">${esc(tag)}</span>` : ""}</div>${body}</section>`;
}
function notice(title, body, kind = "") {
  return `<div class="notice ${kind}"><span class="notice-icon">${kind === "error" ? "!" : "ⓘ"}</span><div><strong>${esc(title)}</strong>${esc(body)}</div></div>`;
}
function selectField(label, name, values, selected = "", placeholder = "Select…") {
  const options = values.map((item) => {
    const value = typeof item === "string" ? item : item.value;
    const text = typeof item === "string" ? item : item.label;
    return `<option value="${esc(value)}" ${value === selected ? "selected" : ""}>${esc(text)}</option>`;
  }).join("");
  return `<div class="field"><label for="${esc(name)}">${esc(label)}</label><select id="${esc(name)}" name="${esc(name)}"><option value="">${esc(placeholder)}</option>${options}</select></div>`;
}
function districtSelect(selected = "") {
  return selectField("District", "district", state.districts, selected, "Choose a district");
}
function cropSelect(selected = "") {
  return selectField("Crop", "crop", state.crops, selected, "Choose a crop");
}
function table(headers, rows, emptyMessage = "No matching records.") {
  if (!rows.length) return empty(emptyMessage);
  return `<div class="table-wrap"><table><thead><tr>${headers.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}
function empty(message, title = "No records available") {
  return `<div class="empty-state"><span class="empty-icon">⌁</span><strong>${esc(title)}</strong><p>${esc(message)}</p></div>`;
}
function limitationList(items = []) {
  if (!items.length) return "";
  return `<ul class="limitation-list">${items.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>`;
}
function statusTag(status) {
  const warning = ["not_collected", "awaiting_upload", "validation_failed", "partially_available"].includes(status);
  return `<span class="tag ${warning ? "warning" : ""}">${esc(String(status || "unknown").replaceAll("_", " "))}</span>`;
}
function chart(values, { color = "#4f875c", label = "Observed values" } = {}) {
  if (!values.length) return empty("No observations are available to plot.");
  const width = 700, height = 205, left = 34, right = 12, top = 12, bottom = 30;
  const numbers = values.map((value) => Number(value) || 0);
  const min = Math.min(...numbers), max = Math.max(...numbers);
  const span = Math.max(max - min, 1);
  const points = numbers.map((value, index) => {
    const x = left + index * (width - left - right) / Math.max(numbers.length - 1, 1);
    const y = top + (max - value) * (height - top - bottom) / span;
    return [x, y];
  });
  const line = points.map(([x, y], index) => `${index ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const area = `${line} L${points.at(-1)[0]},${height - bottom} L${points[0][0]},${height - bottom} Z`;
  const guide = [0, 1, 2, 3].map((i) => {
    const y = top + i * (height - top - bottom) / 3;
    return `<line class="chart-grid" x1="${left}" y1="${y}" x2="${width - right}" y2="${y}"/>`;
  }).join("");
  return `<div class="chart-wrap"><svg class="chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(label)}">
    <defs><linearGradient id="chartGradient" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="${color}" stop-opacity=".20"/><stop offset="1" stop-color="${color}" stop-opacity="0"/></linearGradient></defs>
    ${guide}<path class="chart-fill" d="${area}"/><path class="chart-line" stroke="${color}" d="${line}"/>
    <text class="chart-label" x="${left}" y="${height - 8}">${esc(state.chartStart || "")}</text><text class="chart-label" text-anchor="end" x="${width - right}" y="${height - 8}">${esc(state.chartEnd || "")}</text>
  </svg></div>`;
}
function metric(label, value, note, icon) {
  return `<article class="surface metric-card"><span class="metric-icon">${icon}</span><span class="metric-label">${esc(label)}</span><strong class="metric-value">${esc(value)}</strong><span class="metric-note">${esc(note)}</span></article>`;
}
function setContent(html) {
  content.innerHTML = html;
}
function showError(error) {
  setContent(`${heading(pageLabels[state.page], "The requested information could not be loaded.")}${notice("Data service error", error.message, "error")}`);
}
async function loadPage() {
  pageName.textContent = pageLabels[state.page];
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.page === state.page));
  sidebar.classList.remove("open");
  content.innerHTML = `<div class="loading-state"><span class="spinner"></span>Loading ${esc(pageLabels[state.page].toLowerCase())}…</div>`;
  try {
    const renderers = {
      dashboard: renderDashboard,
      recommendations: renderRecommendations,
      soil: renderSoil,
      weather: renderWeather,
      yield: renderYield,
      market: renderMarket,
      profitability: renderProfitability,
      datasets: renderDatasets,
      models: renderModels,
    };
    await renderers[state.page]();
  } catch (error) {
    showError(error);
  }
}

async function renderDashboard() {
  const data = await api("/api/dashboard");
  state.dashboard = data;
  const m = data.metrics;
  const suitability = await api("/api/recommendations?district=" + encodeURIComponent(state.districts[0] || ""));
  const top = suitability.recommendations.slice(0, 5);
  const bars = top.map((r) => `<div class="bar-row"><span class="bar-label">${esc(r.crop)}</span><div class="bar-track"><div class="bar-value" style="width:${Math.max(0, Math.min(100, r.suitability_score))}%"></div></div><span class="bar-number">${fmt(r.suitability_score, 1)}</span></div>`).join("");
  const gaps = data.data_gaps.length
    ? `${data.data_gaps.slice(0, 4).join(", ")}${data.data_gaps.length > 4 ? ` and ${data.data_gaps.length - 4} more` : ""}.`
    : "All registered data files are available.";
  setContent(`${heading("Agricultural intelligence for Kerala", "A live view of the datasets, evidence, and decision-support tools available in GROW.", "FIELD OVERVIEW")}
    ${notice("Data coverage matters", `Available datasets: ${m.datasets_available} of ${m.datasets_total}. Missing: ${gaps} Recommendations are heuristic compatibility rankings; check their source and limitations before acting.`, "info")}
    <div class="metric-grid">
      ${metric("District profiles", fmt(m.districts_covered), "qualitative soil records", "◈")}
      ${metric("Crop catalog", fmt(m.crops_catalogued), "agronomic requirements", "✳")}
      ${metric("Weather observations", fmt(m.weather_records), "daily historical records", "☼")}
      ${metric("Yield history", fmt(m.yield_records), "observed district records", "↗")}
    </div>
    <div class="grid-two">
      ${panel("Compatibility snapshot", `Top available heuristic scores in ${state.districts[0] || "the selected district"}.`, bars || empty("No suitability records have been ingested."), "not a prediction")}
      <div>
        ${panel("Data pipeline", "Actual files currently available to the application.", `<div class="two-col-list"><div class="info-box"><span>Available files</span><strong>${m.datasets_available} / ${m.datasets_total}</strong></div><div class="info-box"><span>Latest weather date</span><strong>${esc(data.weather_latest_date || "Unavailable")}</strong></div><div class="info-box"><span>Price records</span><strong>${fmt(m.price_records)}</strong></div><div class="info-box"><span>Suitability rows</span><strong>${fmt(m.suitability_records)}</strong></div></div>`)}
        ${panel("Data limitations", "", limitationList(data.limitations))}
      </div>
    </div>
    <p class="small-note">Sources: ${esc(data.weather_source || "weather source unavailable")} for weather, DES Kerala for yield history, and the registered dataset sources shown under Datasets. Dashboard data as of ${esc(data.as_of)}.</p>`);
}

async function renderRecommendations(selectedDistrict = "", selectedSoil = "") {
  const [soils, crops] = await Promise.all([
    api(`/api/soil${selectedDistrict ? `?district=${encodeURIComponent(selectedDistrict)}` : ""}`),
    api("/api/crops"),
  ]);
  state.crops = crops.map((row) => row.crop);
  const matchingSoils = selectedDistrict
    ? soils.profiles.map((row) => row.soil_type)
    : [...new Set(soils.profiles.map((row) => row.soil_type))];
  const soilOptions = matchingSoils.map((soil) => ({ value: soil, label: soil }));
  setContent(`${heading("Find crops suited to a soil profile", "Rank crops from GROW's uploaded compatibility matrix. Scores reflect heuristic soil fit, not a predicted harvest or profit.", "DECISION SUPPORT")}
    ${notice("Interpret scores cautiously", "The matrix uses equal-weight texture, drainage, and estimated pH compatibility. pH estimates are based on qualitative categories; no farm-specific soil test or water availability is used.")}
    ${panel("Recommendation inputs", "Choose a district and, where known, a representative soil profile.", `<form id="recommendation-form" class="form-row">
      ${districtSelect(selectedDistrict)}${selectField("Soil profile (optional)", "soil_type", soilOptions, selectedSoil, "All profiles in district")}
      <button class="button" type="submit">Get recommendations</button></form>`)}
    <div id="recommendation-results">${empty("Choose a district to query the live suitability matrix.", "Ready when you are")}</div>
    <div id="recommendation-limitations"></div>`);
  document.querySelector("#recommendation-form").addEventListener("change", async (event) => {
    if (event.target.name === "district") await renderRecommendations(event.target.value);
  });
  document.querySelector("#recommendation-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const queryString = query({ district: form.get("district"), soil_type: form.get("soil_type") });
    const results = document.querySelector("#recommendation-results");
    results.innerHTML = `<div class="loading-state"><span class="spinner"></span>Looking up the suitability matrix…</div>`;
    try {
      const data = await api(`/api/recommendations?${queryString}`);
      const rows = data.recommendations.map((item) => {
        const score = item.suitability_score;
        return [
          `<strong>${esc(item.crop)}</strong>`,
          `<div class="score-cell"><span class="score-track"><i style="width:${Math.max(0, Math.min(score, 100))}%"></i></span><strong>${fmt(score, 1)}</strong></div>`,
          fmt(item.texture_score, 1),
          fmt(item.drainage_score, 1),
          item.estimated_ph_score == null ? "Not available" : fmt(item.estimated_ph_score, 1),
          esc(item.soil_type),
        ];
      });
      results.innerHTML = panel("Ranked crop compatibility", `${data.recommendations.length} crops from the recorded matrix for ${data.district}${data.soil_type ? ` · ${data.soil_type}` : ""}.`, table(["Crop", "Score / 100", "Texture", "Drainage", "Estimated pH", "Soil profile"], rows), "heuristic");
      document.querySelector("#recommendation-limitations").innerHTML = `<p class="small-note">Provenance: ${esc(data.provenance.dataset)} · ${esc(data.provenance.method)}. ${data.limitations.map(esc).join(" ")}</p>`;
    } catch (error) {
      results.innerHTML = notice("No recommendation could be calculated", error.message, "error");
    }
  });
}

async function renderSoil(selectedDistrict = "") {
  const data = await api(`/api/soil${selectedDistrict ? `?district=${encodeURIComponent(selectedDistrict)}` : ""}`);
  const districtValues = selectedDistrict ? [selectedDistrict] : [...new Set(data.profiles.map((row) => row.district))];
  const profiles = data.profiles.map((row) => [
    esc(row.district), esc(row.soil_type), esc(row.soil_texture), esc(row.drainage),
    esc(row.ph_category), esc(row.organic_matter_category), esc(row.fertility_category),
  ]);
  const cluster = data.cluster
    ? `<div class="info-box"><span>Indicative model cluster</span><strong>${esc(data.cluster.label)}</strong><p class="small-note">${esc(data.cluster.warning)} Silhouette: ${fmt(data.cluster.silhouette, 3)}</p></div>`
    : `<div class="info-box"><span>Cluster model</span><strong>Unavailable</strong><p class="small-note">${esc(data.cluster_error || "No model artifact is available.")}</p></div>`;
  setContent(`${heading("Understand representative soil profiles", "Explore district-level reference characteristics and an optional unsupervised grouping.", "SOIL INTELLIGENCE")}
    ${panel("District profile", "Soil values are qualitative reference descriptions.", `<form id="soil-filter" class="form-row">${districtSelect(selectedDistrict)}<button class="button secondary" type="submit">View profile</button></form>`)}
    <div class="grid-two">
      ${panel("Recorded soil characteristics", `${districtValues.length} profile(s) returned from the soil dataset.`, table(["District", "Soil type", "Texture", "Drainage", "pH category", "Organic matter", "Fertility"], profiles))}
      <div>${panel("Model grouping", "KMeans grouping from the saved soil clustering artifact.", cluster, data.cluster ? "indicative" : "unavailable")}
      ${panel("Limitations", "", limitationList(data.limitations))}</div>
    </div>
    <p class="small-note">Provenance: ${esc(data.provenance)}. Regional soil descriptions are not a substitute for a farm soil test.</p>`);
  document.querySelector("#soil-filter").addEventListener("submit", (event) => {
    event.preventDefault();
    renderSoil(new FormData(event.currentTarget).get("district") || "");
  });
}

async function renderWeather(selectedDistrict = "") {
  const district = selectedDistrict || state.districts[0] || "";
  const data = await api(`/api/weather?district=${encodeURIComponent(district)}`);
  state.chartStart = data.observations[0]?.date || "";
  state.chartEnd = data.observations.at(-1)?.date || "";
  const summary = data.latest_30_day_average;
  const records = data.observations.map((row) => [
    esc(row.date), fmt(row.rainfall_mm, 1), fmt(row.temperature_min_c, 1),
    fmt(row.temperature_max_c, 1), fmt(row.humidity_percent, 1),
  ]);
  setContent(`${heading("Read historical district weather", "Explore daily NASA POWER estimates. This page does not show live conditions or forecasts.", "WEATHER")}
    ${notice("Historical gridded data only", `NASA POWER records for ${data.district} span ${data.date_range[0]} to ${data.date_range[1]}. The latest observations are historical and should not be interpreted as today's weather.`)}
    ${panel("Weather location", "Choose a district with recorded observations.", `<form id="weather-filter" class="form-row">${districtSelect(district)}<button class="button secondary" type="submit">Update</button></form>`)}
    <div class="metric-grid">
      ${metric("Rainfall · 30-day mean", `${fmt(summary.rainfall_mm, 1)} mm`, "per day across latest records", "☂")}
      ${metric("Maximum temperature", `${fmt(summary.temperature_max_c, 1)} °C`, "30-day daily mean", "☼")}
      ${metric("Minimum temperature", `${fmt(summary.temperature_min_c, 1)} °C`, "30-day daily mean", "◌")}
      ${metric("Relative humidity", `${fmt(summary.humidity_percent, 1)}%`, "30-day daily mean", "≈")}
    </div>
    ${panel("Recent daily rainfall", "Observed precipitation (mm), last 30 available records.", chart(data.observations.map((row) => row.rainfall_mm), { label: "Daily rainfall in millimeters" }))}
    ${panel("Recent observations", "Source rows are shown with their original observation dates.", table(["Date", "Rainfall (mm)", "Min temp (°C)", "Max temp (°C)", "Humidity (%)"], records.slice(-12).reverse()))}
    <p class="small-note">Source: ${esc(data.provenance)}. ${data.limitations.map(esc).join(" ")}</p>`);
  document.querySelector("#weather-filter").addEventListener("submit", (event) => {
    event.preventDefault();
    renderWeather(new FormData(event.currentTarget).get("district"));
  });
}

async function renderYield(district = "", crop = "") {
  const data = await api(`/api/yield?${query({ district, crop })}`);
  const availableCrops = [...new Set(data.records.map((row) => row.crop))].sort();
  state.yieldCrops = availableCrops.length ? availableCrops : state.crops;
  const records = data.records;
  state.chartStart = records[0]?.year || "";
  state.chartEnd = records.at(-1)?.year || "";
  const tableRows = records.slice(-14).reverse().map((row) => [
    esc(row.year), esc(row.district), esc(row.crop), fmt(row.yield_kg_per_hectare, 1),
    fmt(row.area_hectares, 1), fmt(row.production_tonnes, 1),
  ]);
  const values = records.slice(-40).map((row) => row.yield_kg_per_hectare);
  setContent(`${heading("Observed crop yield", "Explore reported historical district yield and model validation context; no forward yield estimate is shown.", "YIELD")}
    ${notice("Historical records with an optional baseline reference", "Yield values are reported historical statistics. When a district and crop are selected, the saved district/crop training-mean baseline is shown if available; it is not a weather-aware or season-specific forecast.", "info")}
    ${panel("Filter yield history", "The table lists actual records; use filters to narrow the dataset.", `<form id="yield-filter" class="form-row">${districtSelect(district)}${selectField("Crop", "crop", state.yieldCrops, crop, "All available crops")}<button class="button secondary" type="submit">Apply filters</button></form>`)}
    <div class="metric-grid">
      ${metric("Matching observations", fmt(data.total_matching_records), "available records before table limit", "↗")}
      ${metric("Records displayed", fmt(records.length), "most recent 300 maximum", "▤")}
      ${metric("Latest shown year", records.at(-1)?.year || "—", "historical observation", "◷")}
      ${metric("Baseline reference", data.estimate ? `${fmt(data.estimate.value_kg_per_hectare, 1)} kg/ha` : "Unavailable", data.estimate ? `training mean · ${data.estimate.training_period || "period not recorded"}` : (data.estimate_error || "select district and crop"), "◇")}
    </div>
    <div class="grid-two">
      ${panel("Yield observations", "Historical reported yield (kg/ha); annual records are shown in source order.", chart(values, { label: "Observed historical crop yields" }))}
      ${data.model
        ? panel("Model evaluation", `Best model: ${data.model.best_model || "not recorded"}.`, `<div class="two-col-list"><div class="info-box"><span>Test MAE</span><strong>${fmt(data.model.metrics?.[data.model.best_model]?.mae, 1)} kg/ha</strong></div><div class="info-box"><span>Test R²</span><strong>${fmt(data.model.metrics?.[data.model.best_model]?.r2, 3)}</strong></div></div><p class="small-note">${esc(data.model.data_adequacy || "Evaluation metadata unavailable.")}</p>`, "held-out metrics")
        : empty("No yield model metadata is available.")}
    </div>
    ${panel("Source records", "Actual dataset observations.", table(["Year", "District", "Crop", "Yield (kg/ha)", "Area (ha)", "Production (tonnes)"], tableRows))}
    <p class="small-note">${esc(data.provenance)} ${data.estimate ? esc(data.estimate.interpretation) : ""} ${data.limitations.map(esc).join(" ")}</p>`);
  document.querySelector("#yield-filter").addEventListener("submit", (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    renderYield(form.get("district"), form.get("crop"));
  });
}

async function renderMarket(district = "", crop = "") {
  const data = await api(`/api/market-prices?${query({ district, crop })}`);
  const records = data.records || [];
  const rows = records.slice(-16).reverse().map((row) => [
    esc(row.date), esc(row.district), esc(row.market), esc(row.crop), fmt(row.modal_price, 2), esc(row.price_unit),
  ]);
  const filtering = `<form id="market-filter" class="form-row">${districtSelect(district)}${cropSelect(crop)}<button class="button secondary" type="submit">Apply filters</button></form>`;
  setContent(`${heading("Market price observations", "View uploaded Agmarknet/DMI wholesale prices when authentic records are available.", "MARKET")}
    ${panel("Filter records", "The selection filters source observations only.", filtering)}
    ${data.available
      ? `${data.price_unit_verified === false ? notice("Price unit unverified", data.price_unit_notice || "The source did not supply a price unit. Values are shown unchanged.", "error") : ""}${panel("Matched price observations", `${fmt(data.record_count)} actual record(s) match the filters.`, table(["Date", "District", "Market", "Crop", "Modal price", "Unit"], rows))}<p class="small-note">Source: ${esc(data.provenance)}. These are wholesale quotes, not farm-gate prices.</p>`
      : `${notice("Market-price data unavailable", `${data.reason || "No source records match these filters."} GROW does not display illustrative prices as market data.`, "error")}
        ${panel("Forecast status", "A price forecast is not returned unless sufficient authentic history is available.", `<div class="two-col-list"><div class="info-box"><span>Required records</span><strong>${fmt(data.requirements?.minimum_records)}</strong></div><div class="info-box"><span>Required months</span><strong>${fmt(data.requirements?.minimum_months)}</strong></div></div><p class="small-note">Upload a verified market_prices.csv file in Dataset management. Model assessment is rerun through the existing pipeline separately.</p>`, "deferred")}`}`);
  document.querySelector("#market-filter").addEventListener("submit", (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    renderMarket(form.get("district"), form.get("crop"));
  });
}

async function renderProfitability(district = "", crop = "") {
  const data = await api(`/api/profitability?${query({ district, crop })}`);
  const result = data.available
    ? `<div class="metric-grid">
        ${metric("Historical yield", `${fmt(data.yield_kg_per_hectare, 1)} kg/ha`, "latest recorded district value", "↗")}
        ${metric("Wholesale modal price", `₹${fmt(data.price_inr_per_quintal, 2)}`, `per quintal · ${data.price_date}`, "₹")}
        ${metric("Gross revenue", `₹${fmt(data.gross_revenue_inr_per_hectare, 0)}`, "derived from historical yield × price", "＋")}
        ${metric("Indicative margin", `₹${fmt(data.indicative_margin_inr_per_hectare, 0)}`, "revenue less recorded costs", "◌")}
      </div><p class="small-note">Provenance: ${data.provenance.map(esc).join(" · ")}. This is an indicative gross margin per hectare, not net farm profit; unrecorded costs, quality, timing and realized farm-gate prices are excluded.</p>`
    : notice("Profitability cannot be calculated", data.reason || "Required source data are unavailable.", "error");
  setContent(`${heading("Assess profitability from recorded inputs", "A margin is calculated only when matching real yield, cultivation cost, and price records are present.", "FARM ECONOMICS")}
    ${panel("Analysis inputs", "Select the same district and crop for each joined source.", `<form id="profit-filter" class="form-row">${districtSelect(district)}${cropSelect(crop)}<button class="button" type="submit">Assess profitability</button></form>`)}
    <div id="profit-results">${district && crop ? result : empty("Choose a district and crop to check whether complete cost, yield, and price inputs are available.", "Awaiting analysis")}</div>
    ${data.available ? "" : `<p class="small-note">Currently recorded: ${fmt(data.cost_data_records)} cost rows, ${fmt(data.price_data_records)} price rows, ${fmt(data.demand_data_records)} demand rows. Missing inputs are never replaced with sample values.</p>`}`);
  document.querySelector("#profit-filter").addEventListener("submit", (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    renderProfitability(form.get("district"), form.get("crop"));
  });
}

async function renderDatasets() {
  const datasets = await api("/api/datasets");
  state.datasets = datasets;
  const cards = datasets.map((dataset) => `<article class="surface dataset-card">
    <div><div class="dataset-title">${esc(dataset.name)}</div><div class="dataset-meta">${statusTag(dataset.status)}<span>${fmt(dataset.record_count)} records</span><span>${esc(dataset.category)}</span></div>
      <p class="dataset-description">${esc(dataset.description)}</p>
      <div class="dataset-meta"><span>Source: ${esc(dataset.source_info?.organization || "Not recorded")}</span>${dataset.active_path ? `<span>File: ${esc(dataset.active_path)}</span>` : ""}</div>
      ${dataset.data_quality_limitations?.length ? `<p class="small-note">${esc(dataset.data_quality_limitations[0])}</p>` : ""}
    </div><div class="dataset-actions"><button class="button secondary guidance-button" data-guidance="${esc(dataset.dataset_id)}" type="button">Source guidance</button></div>
    <form class="dataset-upload" data-upload="${esc(dataset.dataset_id)}"><input aria-label="CSV file for ${esc(dataset.name)}" type="file" accept=".csv,text/csv" required><button class="button" type="submit">Validate &amp; upload CSV</button><span class="upload-message small-note" role="status"></span></form>
  </article>`).join("");
  setContent(`${heading("Manage agricultural datasets", "Inspect source coverage and upload authentic CSV records through schema validation.", "DATA MANAGEMENT")}
    ${notice("Safe ingestion", "Each upload is checked against the registered dataset schema. Invalid files are rejected and are not promoted into the active dataset. Valid uploads are archived and become active source data.", "info")}
    <div id="dataset-guidance"></div><div id="dataset-list">${cards}</div>`);
  document.querySelectorAll(".guidance-button").forEach((button) => button.addEventListener("click", async () => {
    try {
      const guidance = await api(`/api/datasets/${encodeURIComponent(button.dataset.guidance)}/guidance`);
      const target = document.querySelector("#dataset-guidance");
      target.innerHTML = `<section class="surface panel"><div class="panel-head"><div><h2>${esc(guidance.name)} · source guidance</h2><p>${esc(guidance.organization)} · <a href="${esc(guidance.official_portal_url)}" target="_blank" rel="noreferrer">Official portal</a></p></div><button class="button secondary" id="close-guidance" type="button">Close</button></div><p class="subtitle">${esc(guidance.instructions)}</p><p class="small-note">Required columns: ${guidance.required_columns.map(esc).join(", ")} · Expected filename: ${esc(guidance.expected_filename)}</p></section>`;
      document.querySelector("#close-guidance").addEventListener("click", () => { target.innerHTML = ""; });
    } catch (error) {
      document.querySelector("#dataset-guidance").innerHTML = notice("Guidance unavailable", error.message, "error");
    }
  }));
  document.querySelectorAll(".dataset-upload").forEach((form) => form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const file = form.querySelector('input[type="file"]').files[0];
    const message = form.querySelector(".upload-message");
    const button = form.querySelector("button");
    if (!file) return;
    button.disabled = true;
    message.textContent = "Validating and ingesting…";
    try {
      const body = new FormData();
      body.append("file", file);
      const response = await fetch(`/api/datasets/${encodeURIComponent(form.dataset.upload)}/upload`, { method: "POST", body });
      const result = await response.json();
      if (!response.ok || !result.success) {
        const issues = result.validation?.validation?.errors || result.validation?.error || result.error || "Validation failed.";
        throw new Error(Array.isArray(issues) ? issues.join(" · ") : issues);
      }
      message.textContent = `${fmt(result.commit.records_committed)} records committed. Refreshing inventory…`;
      await renderDatasets();
    } catch (error) {
      message.textContent = error.message;
      message.style.color = "#9a4d43";
      button.disabled = false;
    }
  }));
}

async function renderModels() {
  const data = await api("/api/models");
  const soil = data.soil, yieldModel = data.yield, price = data.price;
  const cards = [
    soil ? `<article class="surface model-card"><span class="tag warning">low data adequacy</span><h2>Soil clustering</h2><div class="model-score">${fmt(soil.silhouette, 3)}</div><p>Silhouette score · ${fmt(soil.n_records)} profile records · ${fmt(soil.k)} groups. A cluster is not a soil quality grade.</p><dl><dt>Method</dt><dd>${esc(soil.algorithm || "not recorded")}</dd><dt>Features</dt><dd>${fmt(soil.n_features)}</dd></dl><p class="small-note">${esc(soil.data_adequacy || "")} ${esc(soil.interpretation_warning || "")}</p></article>` : empty("No saved soil model metadata.", "Soil model unavailable"),
    yieldModel ? `<article class="surface model-card"><span class="tag">moderate data adequacy</span><h2>Crop yield model</h2><div class="model-score">${esc(yieldModel.best_model || "Not selected")}</div><p>Time-aware held-out evaluation. Train ${fmt(yieldModel.n_train)} records; test ${fmt(yieldModel.n_test)} records.</p><dl><dt>Test period</dt><dd>${esc(yieldModel.test_years || "not recorded")}</dd><dt>MAE</dt><dd>${fmt(yieldModel.metrics?.[yieldModel.best_model]?.mae, 1)} kg/ha</dd><dt>R²</dt><dd>${fmt(yieldModel.metrics?.[yieldModel.best_model]?.r2, 3)}</dd></dl><p class="small-note">${esc(yieldModel.data_adequacy || "")} ${esc(yieldModel.validation_design || "")}</p></article>` : empty("No saved yield model metadata.", "Yield model unavailable"),
    price ? `<article class="surface model-card"><span class="tag warning">${esc(price.status || "not evaluated").replaceAll("_", " ")}</span><h2>Market price assessment</h2><div class="model-score">${fmt(price.record_count)} records</div><p>${esc(price.reason || (price.sufficient_for_modelling ? "Data meet the assessment threshold." : "Authentic data have not met the forecasting threshold."))}</p><dl><dt>Minimum records</dt><dd>${fmt(price.threshold_records)}</dd><dt>Minimum months</dt><dd>${fmt(price.threshold_months)}</dd><dt>Validation design</dt><dd>${esc(price.planned_validation || price.validation_design || "not available")}</dd></dl></article>` : empty("No saved price assessment metadata.", "Price model unavailable"),
  ].join("");
  setContent(`${heading("Model performance & limitations", "Inspect saved evaluation artifacts. Reported metrics are not live predictions.", "MODEL REGISTER")}
    ${notice("Do not interpret evaluation as a guarantee", "Model performance describes a particular historical validation split. It does not establish farm-level accuracy or future performance. Price forecasting is deferred when data are inadequate.", "info")}
    <div class="grid-equal">${cards}</div>
    ${panel("Suitability scoring is not a trained model", "Crop recommendations use the stored rule-based compatibility matrix, independently of the model artifacts.", `<p class="subtitle">Scores combine soil texture, drainage and estimated pH compatibility with equal weighting. No probability, confidence interval, yield estimate, or profitability claim is derived from those values.</p>`)}
    <p class="small-note">Provenance: JSON model metadata and serialized artifacts in the project models/ directory. Refresh this page after retraining or uploading data.</p>`);
}

navigation.addEventListener("click", (event) => {
  const button = event.target.closest("[data-page]");
  if (!button) return;
  event.preventDefault();
  state.page = button.dataset.page;
  loadPage();
});
document.querySelector(".brand").addEventListener("click", (event) => {
  event.preventDefault();
  state.page = "dashboard";
  loadPage();
});
document.querySelector("#mobile-menu").addEventListener("click", () => sidebar.classList.toggle("open"));
document.addEventListener("click", (event) => {
  if (sidebar.classList.contains("open") && !sidebar.contains(event.target) && !event.target.closest("#mobile-menu")) {
    sidebar.classList.remove("open");
  }
});

async function start() {
  document.querySelector("#today").textContent = new Intl.DateTimeFormat("en-IN", { dateStyle: "medium" }).format(new Date());
  try {
    const [districts, crops] = await Promise.all([api("/api/districts"), api("/api/crops")]);
    state.districts = districts;
    state.crops = crops.map((row) => row.crop);
    document.querySelector("#connection-label").textContent = "Data service connected";
    await loadPage();
  } catch (error) {
    document.querySelector("#connection-label").textContent = "Service unavailable";
    showError(error);
  }
}
start();
