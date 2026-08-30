import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './AppShell';
import { HomeView } from '../views/home/HomeView';
import { SimulateView } from '../views/simulate/SimulateView';
import { ResultsView } from '../views/results/ResultsView';
import { CompareView } from '../views/compare/CompareView';
import { RunsView } from '../views/runs/RunsView';

/**
 * All routes are pre-wired. A feature agent fleshing out a view only edits
 * files under `src/views/<name>/` — nothing here needs to change.
 */
export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<HomeView />} />
        <Route path="/simulate" element={<SimulateView />} />
        <Route path="/results" element={<ResultsView />} />
        <Route path="/results/:jobId" element={<ResultsView />} />
        <Route path="/compare" element={<CompareView />} />
        <Route path="/compare/:jobId" element={<CompareView />} />
        <Route path="/runs" element={<RunsView />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
