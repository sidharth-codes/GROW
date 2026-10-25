import React from 'react';
import { PageId } from '../types';

interface SidebarProps {
  activePage: PageId;
  onSelectPage: (page: PageId) => void;
  isOpen: boolean;
  onClose: () => void;
}

const navItems: { id: PageId; label: string; icon: string }[] = [
  { id: 'analyze', label: 'Analyze My Farm', icon: '✦' },
  { id: 'dashboard', label: 'Overview', icon: '▦' },
  { id: 'recommendations', label: 'Crop recommendations', icon: '✳' },
  { id: 'soil', label: 'Soil analysis', icon: '◈' },
  { id: 'weather', label: 'Weather history', icon: '☼' },
  { id: 'yield', label: 'Yield', icon: '↗' },
  { id: 'market', label: 'Market prices', icon: '₹' },
  { id: 'profitability', label: 'Profitability', icon: '◌' },
  { id: 'datasets', label: 'Datasets', icon: '▤' },
  { id: 'models', label: 'Model performance', icon: '⌘' },
];

export const Sidebar: React.FC<SidebarProps> = ({
  activePage,
  onSelectPage,
  isOpen,
  onClose,
}) => {
  return (
    <>
      {isOpen && <div className="sidebar-backdrop" onClick={onClose} />}
      <aside className={`sidebar ${isOpen ? 'open' : ''}`} id="sidebar">
        <div
          className="brand"
          onClick={() => {
            onSelectPage('dashboard');
            onClose();
          }}
          role="button"
          tabIndex={0}
          aria-label="GROW dashboard"
        >
          <span className="brand-mark">G</span>
          <span>
            <strong>GROW</strong>
            <small>Kerala agriculture</small>
          </span>
        </div>

        <div className="nav-label">WORKSPACE</div>

        <nav id="navigation" aria-label="Main navigation">
          {navItems.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${activePage === item.id ? 'active' : ''}`}
              onClick={() => {
                onSelectPage(item.id);
                onClose();
              }}
              type="button"
            >
              <span>{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="source-chip">
            <span className="live-dot"></span>
            <span>Data service connected</span>
          </div>
          <small>Decision support, not a substitute for local agronomic advice.</small>
        </div>
      </aside>
    </>
  );
};
