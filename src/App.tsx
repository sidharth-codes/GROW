import React, { useState } from 'react';
import { PageId } from './types';
import { Sidebar } from './components/Sidebar';
import { Topbar } from './components/Topbar';
import { AnalyzeMyFarmView } from './components/AnalyzeMyFarmView';
import { DashboardView } from './components/DashboardView';
import { RecommendationsView } from './components/RecommendationsView';
import { SoilView } from './components/SoilView';
import { WeatherView } from './components/WeatherView';
import { YieldView } from './components/YieldView';
import { MarketView } from './components/MarketView';
import { ProfitabilityView } from './components/ProfitabilityView';
import { DatasetsView } from './components/DatasetsView';
import { ModelsView } from './components/ModelsView';

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<PageId>('analyze');
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);

  const renderPage = () => {
    switch (activePage) {
      case 'analyze':
        return <AnalyzeMyFarmView />;
      case 'dashboard':
        return <DashboardView onNavigateToAnalyze={() => setActivePage('analyze')} />;
      case 'recommendations':
        return <RecommendationsView />;
      case 'soil':
        return <SoilView />;
      case 'weather':
        return <WeatherView />;
      case 'yield':
        return <YieldView />;
      case 'market':
        return <MarketView />;
      case 'profitability':
        return <ProfitabilityView />;
      case 'datasets':
        return <DatasetsView />;
      case 'models':
        return <ModelsView />;
      default:
        return <DashboardView />;
    }
  };

  return (
    <div className="app-shell">
      <Sidebar
        activePage={activePage}
        onSelectPage={(page) => setActivePage(page)}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="main-area">
        <Topbar
          activePage={activePage}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        />

        <section className="page-content" id="page-content" aria-live="polite">
          {renderPage()}
        </section>
      </main>
    </div>
  );
};

export default App;
