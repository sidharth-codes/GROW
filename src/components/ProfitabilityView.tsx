import React, { useState, useMemo } from 'react';
import { growService } from '../services/growService';
import { fmt } from '../utils/formatters';

export const ProfitabilityView: React.FC = () => {
  const districts = useMemo(() => growService.getDistricts(), []);
  const crops = useMemo(() => growService.getCrops().map((c) => c.crop), []);

  const [selectedDistrict, setSelectedDistrict] = useState<string>('');
  const [selectedCrop, setSelectedCrop] = useState<string>('');
  const [submittedQuery, setSubmittedQuery] = useState<{ district: string; crop: string } | null>(null);

  const data = useMemo(() => {
    return growService.getProfitability(
      submittedQuery?.district || '',
      submittedQuery?.crop || ''
    );
  }, [submittedQuery]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittedQuery({ district: selectedDistrict, crop: selectedCrop });
  };

  return (
    <div>
      <div className="page-heading">
        <div>
          <div className="eyebrow">FARM ECONOMICS</div>
          <h1>Assess profitability from recorded inputs</h1>
          <p className="subtitle">
            A margin is calculated only when matching real yield, cultivation cost, and price
            records are present.
          </p>
        </div>
      </div>

      <section className="surface panel">
        <div className="panel-head">
          <div>
            <h2>Analysis inputs</h2>
            <p>Select the same district and crop for each joined source.</p>
          </div>
        </div>

        <form className="form-row" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="profit-district">District</label>
            <select
              id="profit-district"
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
            <label htmlFor="profit-crop">Crop</label>
            <select
              id="profit-crop"
              name="crop"
              value={selectedCrop}
              onChange={(e) => setSelectedCrop(e.target.value)}
            >
              <option value="">Choose a crop</option>
              {crops.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          <button className="button" type="submit">
            Assess profitability
          </button>
        </form>
      </section>

      {submittedQuery?.district && submittedQuery?.crop ? (
        data.available ? (
          <div>
            <div className="metric-grid">
              <article className="surface metric-card">
                <span className="metric-icon">↗</span>
                <span className="metric-label">Historical yield</span>
                <strong className="metric-value">
                  {fmt(data.yield_kg_per_hectare, 1)} kg/ha
                </strong>
                <span className="metric-note">latest recorded district value</span>
              </article>

              <article className="surface metric-card">
                <span className="metric-icon">₹</span>
                <span className="metric-label">Wholesale modal price</span>
                <strong className="metric-value">
                  ₹{fmt(data.price_inr_per_quintal, 2)}
                </strong>
                <span className="metric-note">per quintal · {data.price_date}</span>
              </article>

              <article className="surface metric-card">
                <span className="metric-icon">＋</span>
                <span className="metric-label">Gross revenue</span>
                <strong className="metric-value">
                  ₹{fmt(data.gross_revenue_inr_per_hectare, 0)}
                </strong>
                <span className="metric-note">historical yield × wholesale price</span>
              </article>

              <article className="surface metric-card">
                <span className="metric-icon">−</span>
                <span className="metric-label">Cultivation cost</span>
                <strong className="metric-value">
                  ₹{fmt(data.cost_inr_per_hectare, 0)}
                </strong>
                <span className="metric-note">per hectare · Kerala DES benchmarks</span>
              </article>

              <article className="surface metric-card" style={{ borderColor: 'var(--green)' }}>
                <span className="metric-icon">◌</span>
                <span className="metric-label">Indicative margin / profit</span>
                <strong className="metric-value" style={{ color: (data.indicative_margin_inr_per_hectare || 0) >= 0 ? '#1b5e20' : '#c62828' }}>
                  {(data.indicative_margin_inr_per_hectare || 0) >= 0 ? '+' : ''}₹{fmt(data.indicative_margin_inr_per_hectare, 0)}
                </strong>
                <span className="metric-note">revenue less recorded costs per hectare</span>
              </article>
            </div>
            <p className="small-note">
              Provenance: {data.provenance?.join(' · ')}. This is an indicative gross margin per
              hectare, not net farm profit; unrecorded costs, quality, timing and realized farm-gate
              prices are excluded.
            </p>
          </div>
        ) : (
          <div className="notice error">
            <span className="notice-icon">!</span>
            <div>
              <strong>Profitability cannot be calculated</strong>
              {data.reason || 'Required source data are unavailable.'}
            </div>
          </div>
        )
      ) : (
        <div className="empty-state">
          <span className="empty-icon">⌁</span>
          <strong>Awaiting analysis</strong>
          <p>
            Choose a district and crop to check whether complete cost, yield, and price inputs are
            available.
          </p>
        </div>
      )}

      <p className="small-note">
        Currently recorded: {fmt(data.cost_data_records)} cost rows, {fmt(data.price_data_records)}{' '}
        price rows, {fmt(data.demand_data_records)} demand rows. Missing inputs are never replaced
        with sample values.
      </p>
    </div>
  );
};
