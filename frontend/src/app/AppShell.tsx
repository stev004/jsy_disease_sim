import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useApiMode } from '../api';
import { Btn } from '../components/Btn';
import { KindChip, StateChip } from '../components/Chip';
import { Seg } from '../components/Seg';
import { useDetail, type DetailLevel } from './DetailProvider';
import { useDrawer } from './Drawer';
import { useScenarioContext } from './ScenarioContextProvider';
import { useTheme } from './ThemeProvider';
import { ShortcutsOverlay } from '../views/drawer';

/** Permanent claim boundary, rendered in the top bar under the product name. */
export const CLAIM_BOUNDARY = 'Synthetic research simulation — not a forecast';

const RAIL = [
  {
    to: '/',
    end: true,
    label: 'Home',
    icon: <path d="M4 11l8-7 8 7v9a1 1 0 0 1-1 1h-5v-6h-4v6H5a1 1 0 0 1-1-1z" />,
  },
  {
    to: '/simulate',
    label: 'Simulate',
    icon: (
      <>
        <circle cx="12" cy="12" r="3" />
        <path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1" />
      </>
    ),
  },
  { to: '/results', label: 'Results', icon: <path d="M4 19V5M4 19h16M8 15l3-4 3 2 4-6" /> },
  {
    to: '/compare',
    label: 'Compare',
    icon: <path d="M9 4v16M15 4v16M4 9h5M15 9h5M4 15h5M15 15h5" />,
  },
  {
    to: '/runs',
    label: 'Runs',
    icon: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 3" />
      </>
    ),
  },
];

const DETAIL_OPTIONS: Array<{ value: DetailLevel; label: string }> = [
  { value: 'simple', label: 'Simple' },
  { value: 'scientific', label: 'Scientific' },
];

export function AppShell() {
  const navigate = useNavigate();
  const { detail, setDetail } = useDetail();
  const { toggleTheme } = useTheme();
  const { openDrawer } = useDrawer();
  const { scenario } = useScenarioContext();
  const mode = useApiMode();

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="mark">JOS</div>
          <div>
            <div className="t1">Jersey Outbreak Simulator</div>
            <div className="t2">{CLAIM_BOUNDARY}</div>
          </div>
        </div>

        <div className="scenario-ctx">
          {scenario && (
            <>
              <span className="scn-name">{scenario.name}</span>
              {scenario.kind && <KindChip kind={scenario.kind} detail={scenario.kindDetail} />}
              {scenario.state && <StateChip state={scenario.state} />}
            </>
          )}
          {mode.usingMock && (
            <span className="chip kind" title="The local API was unreachable; showing demo data.">
              Demo data
            </span>
          )}
        </div>

        <div className="actions">
          <Seg
            options={DETAIL_OPTIONS}
            value={detail}
            onChange={setDetail}
            label="Detail level"
            title="How much scientific detail to show"
          />
          <Btn variant="ghost" title="Toggle theme" onClick={toggleTheme}>
            ◐ Theme
          </Btn>
          <Btn onClick={openDrawer}>Model info</Btn>
          <Btn onClick={() => navigate('/compare')}>Compare</Btn>
          <Btn variant="primary" onClick={() => navigate('/simulate')}>
            New scenario
          </Btn>
        </div>
      </header>

      <nav className="rail" aria-label="Primary">
        {RAIL.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => `nav${isActive ? ' active' : ''}`}
            title={item.label}
          >
            <svg viewBox="0 0 24 24">{item.icon}</svg>
            {item.label}
          </NavLink>
        ))}
        <div className="spacer" />
        <button type="button" className="nav" onClick={openDrawer} title="Assumptions & sources">
          <svg viewBox="0 0 24 24">
            <path d="M12 3l8 4-8 4-8-4zM4 12l8 4 8-4M4 17l8 4 8-4" />
          </svg>
          Model
        </button>
      </nav>

      <main className="stage">
        <Outlet />
      </main>

      <ShortcutsOverlay />
    </div>
  );
}
