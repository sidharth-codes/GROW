import React from 'react';
import { PageId } from '../types';

interface TopbarProps {
  activePage: PageId;
  onToggleSidebar: () => void;
}

const pageTitles: Record<PageId, string> = {
  analyze: 'Analyze My Farm',
  dashboard: 'Overview',
  recommendations: 'Crop recommendations',
  soil: 'Soil analysis',
  weather: 'Weather history',
  yield: 'Yield',
  market: 'Market prices',
  profitability: 'Profitability',
  datasets: 'Datasets',
  models: 'Model performance',
};

export const Topbar: React.FC<TopbarProps> = ({ activePage, onToggleSidebar }) => {
  const todayFormatted = new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
  }).format(new Date());

  return (
    <header className="topbar">
      <button
        className="mobile-menu"
        id="mobile-menu"
        onClick={onToggleSidebar}
        aria-label="Open navigation"
        type="button"
      >
        ☰
      </button>

      <div className="breadcrumb">
        <span>GROW</span>
        <b>/</b>
        <strong id="page-name">{pageTitles[activePage]}</strong>
      </div>

      <div className="topbar-right">
        <span className="location-mark">⌖</span> Kerala, India{' '}
        <span className="topbar-date">{todayFormatted}</span>
      </div>
    </header>
  );
};
