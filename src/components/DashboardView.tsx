import React, { useMemo } from 'react';
import { growService } from '../services/growService';
import { fmt } from '../utils/formatters';

interface DashboardViewProps {
  onNavigateToAnalyze?: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigateToAnalyze }) => {
  const dashboard = useMemo(() => growService.getDashboard(), []);
  const districts = useMemo(() => growService.getDistricts(), []);
  const firstDistrict = districts[0] || 'Thiruvananthapuram';

  const recommendationsData = useMemo(() => {
    try {
      return growService.getRecommendations(firstDistrict);
    } catch {
      return { recommendations: [] };
    }
  }, [firstDistrict]);

  const topSuitability = recommendationsData.recommendations.slice(0, 5);
  const m = dashboard.metrics;

  const gapsText = dashboard.data_gaps.length
    ? `${dashboard.data_gaps.slice(0, 4).join(', ')}${
        dashboard.data_gaps.length > 4 ? ` and ${dashboard.data_gaps.length - 4} more` : ''
      }.`
    : 'All registered data files are available.';

  return (
    <div>
      <div className="page-heading">
        <div>
          <div className="eyebrow">FIELD OVERVIEW</div>
          <h1>Agricultural intelligence for Kerala</h1>
          <p className="subtitle">
            A live view of the datasets, evidence, and decision-support tools available in GROW.
          </p>
        </div>
        {onNavigateToAnalyze && (
          <button
            className="button"
            type="button"
            onClick={onNavigateToAnalyze}
            style={{ whiteSpace: 'nowrap' }}
          >
            ✦ Analyze My Farm
          </button>
        )}
      </div>

      <div
        className="surface panel"
        style={{
          background: 'linear-gradient(135deg, #1d5032 0%, #2e6642 100%)',
          color: '#fff',
          padding: '20px 24px',
          marginBottom: '20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <span style={{ fontSize: '10px', letterSpacing: '0.14em', textTransform: 'uppercase', color: '#a3d8b1', fontWeight: 700 }}>
            Central Farmer Decision Workflow
          </span>
          <h2 style={{ color: '#fff', fontSize: '20px', margin: '4px 0 6px' }}>
            Ready to evaluate your land parcel?
          </h2>
          <p style={{ color: '#d8e8dc', fontSize: '12px', margin: 0, maxWidth: '640px' }}>
            Run the comprehensive <strong>Analyze My Farm</strong> workflow to compute area-scaled harvest production, itemized cultivation costs, verified market price revenue, break-even targets, and risk mitigations for your specific Kerala parcel.
          </p>
        </div>
        {onNavigateToAnalyze && (
          <button
            type="button"
            className="button"
            onClick={onNavigateToAnalyze}
            style={{
              background: '#fff',
              color: 'var(--green-dark)',
              fontSize: '12px',
              padding: '0 20px',
              minHeight: '42px',
              fontWeight: 800,
            }}
          >
            Launch Farm Analysis →
          </button>
        )}
      </div>

      <div className="notice info">
        <span className="notice-icon">ⓘ</span>
        <div>
          <strong>Data coverage matters</strong>
          Available datasets: {m.datasets_available} of {m.datasets_total}. Missing: {gapsText}{' '}
          Recommendations are heuristic compatibility rankings; check their source and limitations
          before acting.
        </div>
      </div>

      <div className="metric-grid">
        <article className="surface metric-card">
          <span className="metric-icon">◈</span>
          <span className="metric-label">District profiles</span>
          <strong className="metric-value">{fmt(m.districts_covered)}</strong>
          <span className="metric-note">qualitative soil records</span>
        </article>

        <article className="surface metric-card">
          <span className="metric-icon">✳</span>
          <span className="metric-label">Crop catalog</span>
          <strong className="metric-value">{fmt(m.crops_catalogued)}</strong>
          <span className="metric-note">agronomic requirements</span>
        </article>

        <article className="surface metric-card">
          <span className="metric-icon">☼</span>
          <span className="metric-label">Weather observations</span>
          <strong className="metric-value">{fmt(m.weather_records)}</strong>
          <span className="metric-note">daily historical records</span>
        </article>

        <article className="surface metric-card">
          <span className="metric-icon">↗</span>
          <span className="metric-label">Yield history</span>
          <strong className="metric-value">{fmt(m.yield_records)}</strong>
          <span className="metric-note">observed district records</span>
        </article>
      </div>

      <div className="grid-two">
        <section className="surface panel">
          <div className="panel-head">
            <div>
              <h2>Compatibility snapshot</h2>
              <p>Top available heuristic scores in {firstDistrict}.</p>
            </div>
            <span className="tag">not a prediction</span>
          </div>
          {topSuitability.length > 0 ? (
            topSuitability.map((r) => (
              <div key={r.crop} className="bar-row">
                <span className="bar-label">{r.crop}</span>
                <div className="bar-track">
                  <div
                    className="bar-value"
                    style={{
                      width: `${Math.max(0, Math.min(100, r.suitability_score))}%`,
                    }}
                  />
                </div>
                <span className="bar-number">{fmt(r.suitability_score, 1)}</span>
              </div>
            ))
          ) : (
            <div className="empty-state">
              <span className="empty-icon">⌁</span>
              <strong>No records available</strong>
              <p>No suitability records have been ingested.</p>
            </div>
          )}
        </section>

        <div>
          <section className="surface panel">
            <div className="panel-head">
              <div>
                <h2>Data pipeline</h2>
                <p>Actual files currently available to the application.</p>
              </div>
            </div>
            <div className="two-col-list">
              <div className="info-box">
                <span>Available files</span>
                <strong>
                  {m.datasets_available} / {m.datasets_total}
                </strong>
              </div>
              <div className="info-box">
                <span>Latest weather date</span>
                <strong>{dashboard.weather_latest_date || 'Unavailable'}</strong>
              </div>
              <div className="info-box">
                <span>Price records</span>
                <strong>{fmt(m.price_records)}</strong>
              </div>
              <div className="info-box">
                <span>Suitability rows</span>
                <strong>{fmt(m.suitability_records)}</strong>
              </div>
            </div>
          </section>

          <section className="surface panel">
            <div className="panel-head">
              <div>
                <h2>Data limitations</h2>
              </div>
            </div>
            <ul className="limitation-list">
              {dashboard.limitations.map((lim, idx) => (
                <li key={idx}>{lim}</li>
              ))}
            </ul>
          </section>
        </div>
      </div>

      <p className="small-note">
        Sources: {dashboard.weather_source || 'weather source unavailable'} for weather, DES Kerala
        for yield history, and the registered dataset sources shown under Datasets. Dashboard data
        as of {dashboard.as_of}.
      </p>
    </div>
  );
};
