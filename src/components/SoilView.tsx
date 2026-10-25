import React, { useState, useMemo } from 'react';
import { growService } from '../services/growService';
import { fmt } from '../utils/formatters';

export const SoilView: React.FC = () => {
  const districts = useMemo(() => growService.getDistricts(), []);
  const [selectedDistrict, setSelectedDistrict] = useState<string>('');

  const data = useMemo(() => {
    return growService.getSoilAnalysis(selectedDistrict || undefined);
  }, [selectedDistrict]);

  const districtValues = selectedDistrict
    ? [selectedDistrict]
    : Array.from(new Set(data.profiles.map((p) => p.district)));

  return (
    <div>
      <div className="page-heading">
        <div>
          <div className="eyebrow">SOIL INTELLIGENCE</div>
          <h1>Understand representative soil profiles</h1>
          <p className="subtitle">
            Explore district-level reference characteristics and an optional unsupervised grouping.
          </p>
        </div>
      </div>

      <section className="surface panel">
        <div className="panel-head">
          <div>
            <h2>District profile</h2>
            <p>Soil values are qualitative reference descriptions.</p>
          </div>
        </div>

        <form
          className="form-row"
          onSubmit={(e) => {
            e.preventDefault();
          }}
        >
          <div className="field">
            <label htmlFor="soil-district">District</label>
            <select
              id="soil-district"
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

          <button
            className="button secondary"
            type="button"
            onClick={() => {}}
          >
            View profile
          </button>
        </form>
      </section>

      <div className="grid-two">
        <section className="surface panel">
          <div className="panel-head">
            <div>
              <h2>Recorded soil characteristics</h2>
              <p>{districtValues.length} profile(s) returned from the soil dataset.</p>
            </div>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>District</th>
                  <th>Soil type</th>
                  <th>Texture</th>
                  <th>Drainage</th>
                  <th>pH category</th>
                  <th>Organic matter</th>
                  <th>Fertility</th>
                </tr>
              </thead>
              <tbody>
                {data.profiles.map((row, idx) => (
                  <tr key={idx}>
                    <td>{row.district}</td>
                    <td>{row.soil_type}</td>
                    <td>{row.soil_texture}</td>
                    <td>{row.drainage}</td>
                    <td>{row.ph_category}</td>
                    <td>{row.organic_matter_category}</td>
                    <td>{row.fertility_category}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <div>
          <section className="surface panel">
            <div className="panel-head">
              <div>
                <h2>Model grouping</h2>
                <p>KMeans grouping from the saved soil clustering artifact.</p>
              </div>
              <span className="tag">indicative</span>
            </div>

            {data.cluster ? (
              <div className="info-box">
                <span>Indicative model cluster</span>
                <strong>{data.cluster.label}</strong>
                <p className="small-note">
                  {data.cluster.warning} Silhouette: {fmt(data.cluster.silhouette, 3)}
                </p>
              </div>
            ) : (
              <div className="info-box">
                <span>Cluster model</span>
                <strong>Unavailable</strong>
                <p className="small-note">No model artifact is available.</p>
              </div>
            )}
          </section>

          <section className="surface panel">
            <div className="panel-head">
              <div>
                <h2>Limitations</h2>
              </div>
            </div>
            <ul className="limitation-list">
              {data.limitations.map((lim, idx) => (
                <li key={idx}>{lim}</li>
              ))}
            </ul>
          </section>
        </div>
      </div>

      <p className="small-note">
        Provenance: {data.provenance}. Regional soil descriptions are not a substitute for a farm
        soil test.
      </p>
    </div>
  );
};
