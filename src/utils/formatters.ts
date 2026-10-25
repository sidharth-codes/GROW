export const fmt = (value: any, digits = 0): string => {
  if (value == null || !Number.isFinite(Number(value))) {
    return '—';
  }
  return Number(value).toLocaleString('en-IN', { maximumFractionDigits: digits });
};

export const statusTagClass = (status: string): string => {
  const warning = [
    'not_collected',
    'awaiting_upload',
    'validation_failed',
    'partially_available',
    'deferred_insufficient_data',
  ].includes(status);
  return `tag ${warning ? 'warning' : ''}`;
};
