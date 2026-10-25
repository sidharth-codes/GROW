import React, { useState, useMemo } from 'react';
import { growService } from '../services/growService';
import { fmt } from '../utils/formatters';

export const RecommendationsView: React.FC = () => {
  const districts = useMemo(() => growService.getDistricts(), []);
  const [selectedDistrict, setSelectedDistrict] = useState<string>('');
  const [selectedSoil, setSelectedSoil] = useState<string>('');
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const availableSoils = useMemo(() => {
    try {
      const data = growService.getSoilAnalysis(selectedDistrict || undefined);
      const types = Array.from(new Set(data.profiles.map((p) => p.soil_type)));
      return types;
    } catch {
      return [];
    }
  }, [selectedDistrict]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDistrict) {
      setError('Select a district to request crop recommendations.');
      setResults(null);
      return;
    }

    try {
      setError(null);
      const recs = growService.getRecommendations(selectedDistrict, selectedSoil || undefined);
      setResults(recs);
    } catch (err: any) {
      setError(err.message || 'No recommendation could be calculated');
      setResults(null);
    }
  };

  return (
    <div>
      <div className="page-heading">
        <div>
          <div className="eyebrow">DECISION SUPPORT</div>
          <h1>Find crops suited to a soil profile</h1>
          <p className="subtitle">
            Rank crops from GROW's uploaded compatibility matrix. Scores reflect heuristic soil fit,
            not a predicted harvest or profit.
          </p>
        </div>
      </div>

      <div className="notice">
        <span className="notice-icon">ⓘ</span>
        <div>
          <strong>Interpret scores cautiously</strong>
          The matrix uses equal-weight texture, drainage, and estimated pH compatibility. pH
          estimates are based on qualitative categories; no farm-specific soil test or water
          availability is used.
        </div>
      </div>

      <section className="surface panel">
        <div className="panel-head">
          <div>
            <h2>Recommendation inputs</h2>
            <p>Choose a district and, where known, a representative soil profile.</p>
          </div>
        </div>

        <form className="form-row" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="rec-district">District</label>
            <select
              id="rec-district"
              name="district"
              value={selectedDistrict}
              onChange={(e) => {
                setSelectedDistrict(e.target.value);
                setSelectedSoil('');
              }}
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
            <label htmlFor="rec-soil">Soil profile (optional)</label>
            <select
              id="rec-soil"
              name="soil_type"
              value={selectedSoil}
              onChange={(e) => setSelectedSoil(e.target.value)}
            >
              <option value="">All profiles in district</option>
              {availableSoils.map((st) => (
                <option key={st} value={st}>
                  {st}
                </option>
              ))}
            </select>
          </div>

          <button className="button" type="submit">
            Get recommendations
          </button>
        </form>
      </section>

      {error && (
        <div className="notice error">
          <span className="notice-icon">!</span>
          <div>
            <strong>No recommendation could be calculated</strong>
            {error}
          </div>
        </div>
      )}

      {results ? (
        <>
          <section className="surface panel">
            <div className="panel-head">
              <div>
                <h2>Ranked crop compatibility</h2>
                <p>
                  {results.recommendations.length} crops from the recorded matrix for{' '}
                  {results.district}
                  {results.soil_type ? ` · ${results.soil_type}` : ''}.
                </p>
              </div>
              <span className="tag">heuristic</span>
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Crop</th>
                    <th>Score / 100</th>
                    <th>Texture</th>
                    <th>Drainage</th>
                    <th>Estimated pH</th>
                    <th>Soil profile</th>
                  </tr>
                </thead>
                <tbody>
                  {results.recommendations.map((item: any, idx: number) => (
                    <tr key={idx}>
                      <td>
                        <strong>{item.crop}</strong>
                      </td>
                      <td>
                        <div className="score-cell">
                          <span className="score-track">
                            <i
                              style={{
                                width: `${Math.max(
                                  0,
                                  Math.min(item.suitability_score, 100)
                                )}%`,
                              }}
                            />
                          </span>
                          <strong>{fmt(item.suitability_score, 1)}</strong>
                        </div>
                      </td>
                      <td>{fmt(item.texture_score, 1)}</td>
                      <td>{fmt(item.drainage_score, 1)}</td>
                      <td>
                        {item.estimated_ph_score == null
                          ? 'Not available'
                          : fmt(item.estimated_ph_score, 1)}
                      </td>
                      <td>{item.soil_type}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <p className="small-note">
            Provenance: {results.provenance.dataset} · {results.provenance.method}.{' '}
            {results.limitations.join(' ')}
          </p>
        </>
      ) : (
        !error && (
          <div className="empty-state">
            <span className="empty-icon">⌁</span>
            <strong>Ready when you are</strong>
            <p>Choose a district to query the live suitability matrix.</p>
          </div>
        )
      )}
    </div>
  );
};
