import React, { useState, useMemo } from 'react';
import { growService } from '../services/growService';
import { fmt } from '../utils/formatters';
import { Chart } from './Chart';

export const YieldView: React.FC = () => {
  const districts = useMemo(() => growService.getDistricts(), []);
  const allCrops = useMemo(() => growService.getCrops().map((c) => c.crop), []);

  const [selectedDistrict, setSelectedDistrict] = useState<string>('');
  const [selectedCrop, setSelectedCrop] = useState<string>('');
  const [appliedFilters, setAppliedFilters] = useState<{ district: string; crop: string }>({
    district: '',
    crop: '',
  });

  const data = useMemo(() => {
    return growService.getYieldHistory(appliedFilters.district, appliedFilters.crop);
  }, [appliedFilters]);

  const availableCrops = useMemo(() => {
    const list = Array.from(new Set(data.records.map((r) => r.crop))).sort();
    return list.length ? list : allCrops;
  }, [data.records, allCrops]);

  const handleApply = (e: React.FormEvent) => {
    e.preventDefault();
    setAppliedFilters({ district: selectedDistrict, crop: selectedCrop });
  };

  const records = data.records;
  const tableRows = useMemo(() => records.slice(-14).reverse(), [records]);
  const chartValues = useMemo(() => records.slice(-40).map((r) => r.yield_kg_per_hectare || 0), [records]);

  return (
    <div>
      <div className="page-heading">
        <div>
          <div className="eyebrow">YIELD</div>
          <h1>Observed crop yield</h1>
          <p className="subtitle">
            Explore reported historical district yield and model validation context; no forward
            yield estimate is shown.
          </p>
        </div>
      </div>

      <div className="notice info">
        <span className="notice-icon">ⓘ</span>
        <div>
          <strong>Historical records with an optional baseline reference</strong>
          Yield values are reported historical statistics. When a district and crop are selected,
          the saved district/crop training-mean baseline is shown if available; it is not a
          weather-aware or season-specific forecast.
        </div>
      </div>

      <section className="surface panel">
        <div className="panel-head">
          <div>
            <h2>Filter yield history</h2>
            <p>The table lists actual records; use filters to narrow the dataset.</p>
          </div>
        </div>

        <form className="form-row" onSubmit={handleApply}>
          <div className="field">
            <label htmlFor="yield-district">District</label>
            <select
              id="yield-district"
              name="district"
              value={selectedDistrict}
              onChange={(e) => setSelectedDistrict(e.target.value)}
            >
              <option value="">Choose a district</option>
              {districts.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label htmlFor="yield-crop">Crop</label>
            <select
              id="yield-crop"
              name="crop"
              value={selectedCrop}
              onChange={(e) => setSelectedCrop(e.target.value)}
            >
              <option value="">All available crops</option>
              {availableCrops.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          <button className="button secondary" type="submit">
            Apply filters
          </button>
        </form>
      </section>

      <div className="metric-grid">
        <article className="surface metric-card">
          <span className="metric-icon">↗</span>
          <span className="metric-label">Matching observations</span>
          <strong className="metric-value">{fmt(data.total_matching_records)}</strong>
          <span className="metric-note">available records before table limit</span>
        </article>

        <article className="surface metric-card">
          <span className="metric-icon">▤</span>
          <span className="metric-label">Records displayed</span>
          <strong className="metric-value">{fmt(records.length)}</strong>
          <span className="metric-note">most recent 300 maximum</span>
        </article>

        <article className="surface metric-card">
          <span className="metric-icon">◷</span>
          <span className="metric-label">Latest shown year</span>
          <strong className="metric-value">{records[records.length - 1]?.year || '—'}</strong>
          <span className="metric-note">historical observation</span>
        </article>

        <article className="surface metric-card">
          <span className="metric-icon">◇</span>
          <span className="metric-label">Baseline reference</span>
          <strong className="metric-value">
            {data.estimate
              ? `${fmt(data.estimate.value_kg_per_hectare, 1)} kg/ha`
              : 'Unavailable'}
          </strong>
          <span className="metric-note">
            {data.estimate
              ? `training mean · ${data.estimate.training_period || 'period not recorded'}`
              : data.estimate_error || 'select district and crop'}
          </span>
        </article>
      </div>

      <div className="grid-two">
        <section className="surface panel">
          <div className="panel-head">
            <div>
              <h2>Yield observations</h2>
              <p>Historical reported yield (kg/ha); annual records are shown in source order.</p>
            </div>
          </div>
          <Chart
            values={chartValues}
            label="Observed historical crop yields"
            startLabel={records[0]?.year || ''}
            endLabel={records[records.length - 1]?.year || ''}
          />
        </section>

        {data.model && (
          <section className="surface panel">
            <div className="panel-head">
              <div>
                <h2>Model evaluation</h2>
                <p>Best model: {data.model.best_model || 'not recorded'}.</p>
              </div>
              <span className="tag">held-out metrics</span>
            </div>
            <div className="two-col-list">
              <div className="info-box">
                <span>Test MAE</span>
                <strong>
                  {fmt((data.model.metrics as any)?.[data.model.best_model]?.mae, 1)} kg/ha
                </strong>
              </div>
              <div className="info-box">
                <span>Test R²</span>
                <strong>
                  {fmt((data.model.metrics as any)?.[data.model.best_model]?.r2, 3)}
                </strong>
              </div>
            </div>
            <p className="small-note">
              {data.model.data_adequacy || 'Evaluation metadata unavailable.'}
            </p>
          </section>
        )}
      </div>

      <section className="surface panel">
        <div className="panel-head">
          <div>
            <h2>Source records</h2>
            <p>Actual dataset observations.</p>
          </div>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Year</th>
                <th>District</th>
                <th>Crop</th>
                <th>Yield (kg/ha)</th>
                <th>Area (ha)</th>
                <th>Production (tonnes)</th>
              </tr>
            </thead>
            <tbody>
              {tableRows.map((row, idx) => (
                <tr key={idx}>
                  <td>{row.year}</td>
                  <td>{row.district}</td>
                  <td>{row.crop}</td>
                  <td>{fmt(row.yield_kg_per_hectare, 1)}</td>
                  <td>{fmt(row.area_hectares, 1)}</td>
                  <td>{fmt(row.production_tonnes, 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <p className="small-note">
        {data.provenance} {data.estimate ? data.estimate.interpretation : ''}{' '}
        {data.limitations.join(' ')}
      </p>
    </div>
  );
};
