import React, { useMemo } from 'react';
import { growService } from '../services/growService';
import { fmt, statusTagClass } from '../utils/formatters';

export const ModelsView: React.FC = () => {
  const models = useMemo(() => growService.getModelPerformance(), []);
  const soil = models.soil;
  const yieldModel = models.yield;
  const price = models.price;

  return (
    <div>
      <div className="page-heading">
        <div>
          <div className="eyebrow">MODEL REGISTER</div>
          <h1>Model performance &amp; limitations</h1>
          <p className="subtitle">
            Inspect saved evaluation artifacts. Reported metrics are not live predictions.
          </p>
        </div>
      </div>

      <div className="notice info">
        <span className="notice-icon">ⓘ</span>
        <div>
          <strong>Do not interpret evaluation as a guarantee</strong>
          Model performance describes a particular historical validation split. It does not
          establish farm-level accuracy or future performance. Price forecasting is deferred when
          data are inadequate.
        </div>
      </div>

      <div className="grid-equal">
        {soil ? (
          <article className="surface model-card">
            <span className="tag warning">low data adequacy</span>
            <h2>Soil clustering</h2>
            <div className="model-score">{fmt(soil.silhouette, 3)}</div>
            <p>
              Silhouette score · {fmt(soil.n_records)} profile records · {fmt(soil.k)} groups. A
              cluster is not a soil quality grade.
            </p>
            <dl>
              <dt>Method</dt>
              <dd>{soil.algorithm || 'not recorded'}</dd>
              <dt>Features</dt>
              <dd>{fmt(soil.n_features)}</dd>
            </dl>
            <p className="small-note">
              {soil.data_adequacy || ''} {soil.interpretation_warning || ''}
            </p>
          </article>
        ) : (
          <div className="empty-state">
            <span className="empty-icon">⌁</span>
            <strong>Soil model unavailable</strong>
            <p>No saved soil model metadata.</p>
          </div>
        )}

        {yieldModel ? (
          <article className="surface model-card">
            <span className="tag">moderate data adequacy</span>
            <h2>Crop yield model</h2>
            <div className="model-score">{yieldModel.best_model || 'Not selected'}</div>
            <p>
              Time-aware held-out evaluation. Train {fmt(yieldModel.n_train)} records; test{' '}
              {fmt(yieldModel.n_test)} records.
            </p>
            <dl>
              <dt>Test period</dt>
              <dd>{yieldModel.test_years || 'not recorded'}</dd>
              <dt>MAE</dt>
              <dd>
                {fmt(
                  (yieldModel.metrics as any)?.[yieldModel.best_model]?.mae,
                  1
                )} kg/ha
              </dd>
              <dt>R²</dt>
              <dd>
                {fmt(
                  (yieldModel.metrics as any)?.[yieldModel.best_model]?.r2,
                  3
                )}
              </dd>
            </dl>
            <p className="small-note">
              {yieldModel.data_adequacy || ''} {yieldModel.validation_design || ''}
            </p>
          </article>
        ) : (
          <div className="empty-state">
            <span className="empty-icon">⌁</span>
            <strong>Yield model unavailable</strong>
            <p>No saved yield model metadata.</p>
          </div>
        )}

        {price ? (
          <article className="surface model-card">
            <span className={statusTagClass(price.status || 'not_evaluated')}>
              {(price.status || 'not evaluated').replace(/_/g, ' ')}
            </span>
            <h2>Market price assessment</h2>
            <div className="model-score">{fmt(price.record_count)} records</div>
            <p>
              {price.reason ||
                ((price as any).sufficient_for_modelling
                  ? 'Data meet the assessment threshold.'
                  : 'Authentic data have not met the forecasting threshold.')}
            </p>
            <dl>
              <dt>Minimum records</dt>
              <dd>{fmt(price.threshold_records)}</dd>
              <dt>Minimum months</dt>
              <dd>{fmt(price.threshold_months)}</dd>
              <dt>Validation design</dt>
              <dd>{price.planned_validation || (price as any).validation_design || 'not available'}</dd>
            </dl>
          </article>
        ) : (
          <div className="empty-state">
            <span className="empty-icon">⌁</span>
            <strong>Price model unavailable</strong>
            <p>No saved price assessment metadata.</p>
          </div>
        )}
      </div>

      <section className="surface panel" style={{ marginTop: '16px' }}>
        <div className="panel-head">
          <div>
            <h2>Suitability scoring is not a trained model</h2>
            <p>
              Crop recommendations use the stored rule-based compatibility matrix, independently of
              the model artifacts.
            </p>
          </div>
        </div>
        <p className="subtitle">
          Scores combine soil texture, drainage and estimated pH compatibility with equal weighting.
          No probability, confidence interval, yield estimate, or profitability claim is derived
          from those values.
        </p>
      </section>

      <p className="small-note">
        Provenance: JSON model metadata and serialized artifacts in the project models/ directory.
        Refresh this page after retraining or uploading data.
      </p>
    </div>
  );
};
