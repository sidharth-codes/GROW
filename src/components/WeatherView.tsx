import React, { useState, useMemo } from 'react';
import { growService } from '../services/growService';
import { fmt } from '../utils/formatters';
import { Chart } from './Chart';

export const WeatherView: React.FC = () => {
  const districts = useMemo(() => growService.getDistricts(), []);
  const [selectedDistrict, setSelectedDistrict] = useState<string>(districts[0] || 'Alappuzha');

  const data = useMemo(() => {
    return growService.getWeather(selectedDistrict);
  }, [selectedDistrict]);

  const summary = data.latest_30_day_average;
  const recentRecords = useMemo(() => {
    return data.observations.slice(-12).reverse();
  }, [data.observations]);

  const rainfallValues = useMemo(() => {
    return data.observations.map((row) => row.rainfall_mm);
  }, [data.observations]);

  return (
    <div>
      <div className="page-heading">
        <div>
          <div className="eyebrow">WEATHER</div>
          <h1>Read historical district weather</h1>
          <p className="subtitle">
            Explore daily NASA POWER estimates. This page does not show live conditions or forecasts.
          </p>
        </div>
      </div>

      <div className="notice">
        <span className="notice-icon">ⓘ</span>
        <div>
          <strong>Historical gridded data only</strong>
          NASA POWER records for {data.district} span {data.date_range[0]} to {data.date_range[1]}.
          The latest observations are historical and should not be interpreted as today's weather.
        </div>
      </div>

      <section className="surface panel">
        <div className="panel-head">
          <div>
            <h2>Weather location</h2>
            <p>Choose a district with recorded observations.</p>
          </div>
        </div>

        <form
          className="form-row"
          onSubmit={(e) => {
            e.preventDefault();
          }}
        >
          <div className="field">
            <label htmlFor="weather-district">District</label>
            <select
              id="weather-district"
              name="district"
              value={selectedDistrict}
              onChange={(e) => setSelectedDistrict(e.target.value)}
            >
              {districts.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          <button className="button secondary" type="button">
            Update
          </button>
        </form>
      </section>

      <div className="metric-grid">
        <article className="surface metric-card">
          <span className="metric-icon">☂</span>
          <span className="metric-label">Rainfall · 30-day mean</span>
          <strong className="metric-value">{fmt(summary.rainfall_mm, 1)} mm</strong>
          <span className="metric-note">per day across latest records</span>
        </article>

        <article className="surface metric-card">
          <span className="metric-icon">☼</span>
          <span className="metric-label">Maximum temperature</span>
          <strong className="metric-value">{fmt(summary.temperature_max_c, 1)} °C</strong>
          <span className="metric-note">30-day daily mean</span>
        </article>

        <article className="surface metric-card">
          <span className="metric-icon">◌</span>
          <span className="metric-label">Minimum temperature</span>
          <strong className="metric-value">{fmt(summary.temperature_min_c, 1)} °C</strong>
          <span className="metric-note">30-day daily mean</span>
        </article>

        <article className="surface metric-card">
          <span className="metric-icon">≈</span>
          <span className="metric-label">Relative humidity</span>
          <strong className="metric-value">{fmt(summary.humidity_percent, 1)}%</strong>
          <span className="metric-note">30-day daily mean</span>
        </article>
      </div>

      <section className="surface panel">
        <div className="panel-head">
          <div>
            <h2>Recent daily rainfall</h2>
            <p>Observed precipitation (mm), last 30 available records.</p>
          </div>
        </div>
        <Chart
          values={rainfallValues}
          label="Daily rainfall in millimeters"
          startLabel={data.observations[0]?.date || ''}
          endLabel={data.observations[data.observations.length - 1]?.date || ''}
        />
      </section>

      <section className="surface panel">
        <div className="panel-head">
          <div>
            <h2>Recent observations</h2>
            <p>Source rows are shown with their original observation dates.</p>
          </div>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Rainfall (mm)</th>
                <th>Min temp (°C)</th>
                <th>Max temp (°C)</th>
                <th>Humidity (%)</th>
              </tr>
            </thead>
            <tbody>
              {recentRecords.map((row, idx) => (
                <tr key={idx}>
                  <td>{row.date}</td>
                  <td>{fmt(row.rainfall_mm, 1)}</td>
                  <td>{fmt(row.temperature_min_c, 1)}</td>
                  <td>{fmt(row.temperature_max_c, 1)}</td>
                  <td>{fmt(row.humidity_percent, 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <p className="small-note">
        Source: {data.provenance}. {data.limitations.join(' ')}
      </p>
    </div>
  );
};
