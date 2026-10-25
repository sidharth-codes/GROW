import React, { useState } from 'react';
import { growService } from '../services/growService';
import { fmt, statusTagClass } from '../utils/formatters';

export const DatasetsView: React.FC = () => {
  const [datasets, setDatasets] = useState(() => growService.getDatasets());
  const [activeGuidanceId, setActiveGuidanceId] = useState<string | null>(null);
  const [uploadMessages, setUploadMessages] = useState<
    Record<string, { text: string; isError?: boolean }>
  >({});
  const [uploadingId, setUploadingId] = useState<string | null>(null);

  const guidanceData = activeGuidanceId
    ? growService.getDatasetGuidance(activeGuidanceId)
    : null;

  const handleFileUpload = async (datasetId: string, file: File) => {
    if (!file) return;

    setUploadingId(datasetId);
    setUploadMessages((prev) => ({
      ...prev,
      [datasetId]: { text: 'Validating and ingesting…' },
    }));

    try {
      const text = await file.text();
      const result = growService.uploadDataset(datasetId, file.name, text);

      if (!result.success) {
        const issues =
          result.validation?.validation?.errors?.join(' · ') ||
          result.validation?.error ||
          'Validation failed.';
        setUploadMessages((prev) => ({
          ...prev,
          [datasetId]: { text: issues, isError: true },
        }));
      } else {
        const committedCount = result.commit?.records_committed || 0;
        setUploadMessages((prev) => ({
          ...prev,
          [datasetId]: {
            text: `${fmt(committedCount)} records committed. Refreshing inventory…`,
            isError: false,
          },
        }));
        // Refresh dataset inventory
        setDatasets(growService.getDatasets());
      }
    } catch (err: any) {
      setUploadMessages((prev) => ({
        ...prev,
        [datasetId]: { text: err.message || 'Upload failed.', isError: true },
      }));
    } finally {
      setUploadingId(null);
    }
  };

  return (
    <div>
      <div className="page-heading">
        <div>
          <div className="eyebrow">DATA MANAGEMENT</div>
          <h1>Manage agricultural datasets</h1>
          <p className="subtitle">
            Inspect source coverage and upload authentic CSV records through schema validation.
          </p>
        </div>
      </div>

      <div className="notice info">
        <span className="notice-icon">ⓘ</span>
        <div>
          <strong>Safe ingestion</strong>
          Each upload is checked against the registered dataset schema. Invalid files are rejected
          and are not promoted into the active dataset. Valid uploads are archived and become
          active source data.
        </div>
      </div>

      {guidanceData && (
        <section className="surface panel" id="dataset-guidance">
          <div className="panel-head">
            <div>
              <h2>{guidanceData.name} · source guidance</h2>
              <p>
                {guidanceData.organization} ·{' '}
                <a
                  href={guidanceData.official_portal_url}
                  target="_blank"
                  rel="noreferrer"
                  style={{ color: 'var(--green-dark)', fontWeight: 600 }}
                >
                  Official portal
                </a>
              </p>
            </div>
            <button
              className="button secondary"
              type="button"
              onClick={() => setActiveGuidanceId(null)}
            >
              Close
            </button>
          </div>
          <p className="subtitle">{guidanceData.instructions}</p>
          <p className="small-note">
            Required columns: {guidanceData.required_columns.join(', ')} · Expected filename:{' '}
            {guidanceData.expected_filename}
          </p>
        </section>
      )}

      <div id="dataset-list">
        {datasets.map((dataset) => {
          const uploadStatus = uploadMessages[dataset.dataset_id];

          return (
            <article key={dataset.dataset_id} className="surface dataset-card">
              <div>
                <div className="dataset-title">{dataset.name}</div>
                <div className="dataset-meta">
                  <span className={statusTagClass(dataset.status)}>
                    {dataset.status.replace(/_/g, ' ')}
                  </span>
                  <span>{fmt(dataset.record_count)} records</span>
                  <span>{dataset.category}</span>
                </div>
                <p className="dataset-description">{dataset.description}</p>
                <div className="dataset-meta">
                  <span>
                    Source: {dataset.source_info?.organization || 'Not recorded'}
                  </span>
                  {dataset.active_path && <span>File: {dataset.active_path}</span>}
                </div>
                {dataset.data_quality_limitations &&
                  dataset.data_quality_limitations.length > 0 && (
                    <p className="small-note">{dataset.data_quality_limitations[0]}</p>
                  )}
              </div>

              <div className="dataset-actions">
                <button
                  className="button secondary guidance-button"
                  type="button"
                  onClick={() =>
                    setActiveGuidanceId(
                      activeGuidanceId === dataset.dataset_id ? null : dataset.dataset_id
                    )
                  }
                >
                  Source guidance
                </button>
              </div>

              <form
                className="dataset-upload"
                onSubmit={(e) => {
                  e.preventDefault();
                  const form = e.currentTarget;
                  const fileInput = form.querySelector('input[type="file"]') as HTMLInputElement;
                  if (fileInput?.files?.[0]) {
                    handleFileUpload(dataset.dataset_id, fileInput.files[0]);
                  }
                }}
              >
                <input
                  aria-label={`CSV file for ${dataset.name}`}
                  type="file"
                  accept=".csv,text/csv"
                  required
                />
                <button
                  className="button"
                  type="submit"
                  disabled={uploadingId === dataset.dataset_id}
                >
                  Validate &amp; upload CSV
                </button>
                {uploadStatus && (
                  <span
                    className="upload-message small-note"
                    role="status"
                    style={{
                      color: uploadStatus.isError ? '#9a4d43' : 'inherit',
                      fontWeight: uploadStatus.isError ? 600 : 'normal',
                    }}
                  >
                    {uploadStatus.text}
                  </span>
                )}
              </form>
            </article>
          );
        })}
      </div>
    </div>
  );
};
