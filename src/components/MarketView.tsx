import React, { useState, useMemo } from 'react';
import { growService } from '../services/growService';
import { fmt } from '../utils/formatters';

export const MarketView: React.FC = () => {
  const districts = useMemo(() => growService.getDistricts(), []);
  const crops = useMemo(() => growService.getCrops().map((c) => c.crop), []);

  const [selectedDistrict, setSelectedDistrict] = useState<string>('');
  const [selectedCrop, setSelectedCrop] = useState<string>('');
  const [appliedFilters, setAppliedFilters] = useState<{ district: string; crop: string }>({
    district: '',
    crop: '',
  });

  const data = useMemo(() => {
    return growService.getMarketPrices(appliedFilters.district, appliedFilters.crop);
  }, [appliedFilters]);

  const handleApply = (e: React.FormEvent) => {
    e.preventDefault();
    setAppliedFilters({ district: selectedDistrict, crop: selectedCrop });
  };

  const records = data.records || [];
  const rows = useMemo(() => records.slice(-16).reverse(), [records]);

  return (
    <div>
      <div className="page-heading">
        <div>
          <div className="eyebrow">MARKET</div>
          <h1>Market price observations</h1>
          <p className="subtitle">
            View uploaded Agmarknet/DMI wholesale prices when authentic records are available.
          </p>
        </div>
      </div>

      <section className="surface panel">
        <div className="panel-head">
          <div>
            <h2>Filter records</h2>
            <p>The selection filters source observations only.</p>
          </div>
        </div>

        <form className="form-row" onSubmit={handleApply}>
          <div className="field">
            <label htmlFor="market-district">District</label>
            <select
              id="market-district"
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
            <label htmlFor="market-crop">Crop</label>
            <select
              id="market-crop"
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

          <button className="button secondary" type="submit">
            Apply filters
          </button>
        </form>
      </section>

      {data.available ? (
        <>
          {!data.price_unit_verified && (
            <div className="notice error">
              <span className="notice-icon">!</span>
              <div>
                <strong>Price unit unverified</strong>
                {data.price_unit_notice ||
                  'The source did not supply a price unit. Values are shown unchanged.'}
              </div>
            </div>
          )}

          <section className="surface panel">
            <div className="panel-head">
              <div>
                <h2>Matched price observations</h2>
                <p>{fmt(data.record_count)} actual record(s) match the filters.</p>
              </div>
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>District</th>
                    <th>Market</th>
                    <th>Crop</th>
                    <th>Modal price</th>
                    <th>Unit</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, idx) => (
                    <tr key={idx}>
                      <td>{row.date}</td>
                      <td>{row.district}</td>
                      <td>{row.market}</td>
                      <td>{row.crop}</td>
                      <td>{fmt(row.modal_price, 2)}</td>
                      <td>{row.price_unit}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <p className="small-note">
            Source: {data.provenance}. These are wholesale quotes, not farm-gate prices.
          </p>
        </>
      ) : (
        <>
          <div className="notice error">
            <span className="notice-icon">!</span>
            <div>
              <strong>Market-price data unavailable</strong>
              {data.reason || 'No source records match these filters.'} GROW does not display
              illustrative prices as market data.
            </div>
          </div>

          <section className="surface panel">
            <div className="panel-head">
              <div>
                <h2>Forecast status</h2>
                <p>
                  A price forecast is not returned unless sufficient authentic history is available.
                </p>
              </div>
              <span className="tag">deferred</span>
            </div>
            <div className="two-col-list">
              <div className="info-box">
                <span>Required records</span>
                <strong>{fmt(data.requirements?.minimum_records)}</strong>
              </div>
              <div className="info-box">
                <span>Required months</span>
                <strong>{fmt(data.requirements?.minimum_months)}</strong>
              </div>
            </div>
            <p className="small-note">
              Upload a verified market_prices.csv file in Dataset management. Model assessment is
              rerun through the existing pipeline separately.
            </p>
          </section>
        </>
      )}
    </div>
  );
};
