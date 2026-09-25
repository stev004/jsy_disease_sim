import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import '../styles/motion.css';
import { useApiMode } from '../api';
import { Btn } from '../components/Btn';
import { jobKindLabel, jobStateLabel } from '../components/Chip';
import { Seg } from '../components/Seg';
import { useDetail, type DetailLevel } from './DetailProvider';
import { useDrawer } from './Drawer';
import { useScenarioContext } from './ScenarioContextProvider';
import { useTheme } from './ThemeProvider';
import { ShortcutsOverlay } from '../views/drawer';

/** Permanent claim boundary, rendered in the top bar and on relevant pages. */
export const CLAIM_BOUNDARY = 'Synthetic research simulation — not a forecast';

const PRIMARY_NAV = [
  { to: '/', end: true, label: 'Home' },
  { to: '/simulate', label: 'Simulate' },
  { to: '/results', label: 'Results' },
  { to: '/compare', label: 'Compare' },
  { to: '/runs', label: 'Runs & evidence' },
];

const DETAIL_OPTIONS: Array<{ value: DetailLevel; label: string }> = [
  { value: 'simple', label: 'Simple' },
  { value: 'scientific', label: 'Scientific' },
];

function ScenarioSummary({ compact = false }: { compact?: boolean }) {
  const { scenario } = useScenarioContext();
  if (!scenario) return null;
  const running = scenario.state === 'RUNNING' || scenario.state === 'CANCEL_REQUESTED';
  const stateClass = scenario.state?.toLowerCase().replaceAll('_', '-');
  return (
    <span className="chip scenario-chip" role="group" aria-label="Current scenario">
      <span className="scn-name">{scenario.name}</span>
      {scenario.kind && (
        <span className="scenario-kind">
          {jobKindLabel(scenario.kind)}{scenario.kindDetail ? ` · ${scenario.kindDetail}` : ''}
        </span>
      )}
      {scenario.state && (
        <span className={`scenario-state ${stateClass}`}>
          <span className={`scenario-state-dot${running ? ' pulse' : ''}`} aria-hidden="true" />
          {jobStateLabel(scenario.state)}
        </span>
      )}
      {compact && scenario.jobId && <span className="mono scenario-id">{scenario.jobId}</span>}
    </span>
  );
}

export function AppShell() {
  const navigate = useNavigate();
  const { detail, setDetail } = useDetail();
  const { toggleTheme, theme } = useTheme();
  const { openDrawer } = useDrawer();
  const { scenario } = useScenarioContext();
  const mode = useApiMode();

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand-lockup">
          <Link className="brand" to="/" aria-label="JOS home">
            <span className="mark" aria-hidden="true"><span /></span>
            <span className="brand-copy">
              <span className="brand-line-one">
                <span className="brand-code">JOS</span>
                <span className="brand-name">Jersey Outbreak Simulator</span>
              </span>
            </span>
          </Link>
          <span className="brand-disclaimer">{CLAIM_BOUNDARY}</span>
        </div>

        <nav className="primary-nav" aria-label="Primary navigation">
          {PRIMARY_NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `nav-tab${isActive ? ' active' : ''}`}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="topbar-context">
          <span className="context-spacer" aria-hidden="true" />
          {mode.usingMock && (
            <span className="chip accent demo-chip" title="The local API was unreachable; showing demo data.">
              Demo data
            </span>
          )}

          {scenario && (
            <div className="scenario-context scenario-context-expanded">
              <ScenarioSummary />
            </div>
          )}
          {scenario && (
            <details className="scenario-menu">
              <summary aria-label="Current run">Current run <span aria-hidden="true">⌄</span></summary>
              <div className="scenario-menu-content">
                <ScenarioSummary compact />
              </div>
            </details>
          )}
        </div>

        <div className="topbar-controls">
          <Seg
            options={DETAIL_OPTIONS}
            value={detail}
            onChange={setDetail}
            label="Detail level"
            title="How much scientific detail to show"
            className="detail-toggle"
          />
          <Btn
            variant="ghost"
            className="theme-toggle"
            aria-label="Toggle theme"
            title={`Switch to ${theme === 'dark' ? 'Notebook light' : 'Harbour dark'} theme`}
            onClick={toggleTheme}
          >
            <span aria-hidden="true">{theme === 'dark' ? '◐' : '◑'}</span>
          </Btn>
          <Btn
            className="model-info-button"
            aria-label="Model info"
            title="Open model info"
            onClick={openDrawer}
          >
            <span className="model-info-label">Model info</span>
            <span className="model-info-icon" aria-hidden="true">ⓘ</span>
          </Btn>
          <Btn variant="primary" onClick={() => navigate('/simulate')}>
            New scenario
          </Btn>
        </div>
      </header>

      <main className="stage">
        <Outlet />
      </main>

      <ShortcutsOverlay />
    </div>
  );
}
