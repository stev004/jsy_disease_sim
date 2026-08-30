import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import type { JobKind, JobState } from '../api/types';

/**
 * The "current scenario" shown in the top bar. A view (usually Results or
 * Compare) declares it with `useScenarioContextEffect(...)`; it clears itself
 * when that view unmounts, so no other file needs touching.
 */
export interface ScenarioContextValue {
  name: string;
  kind?: JobKind;
  /** e.g. "5 seeds" — rendered after the kind. */
  kindDetail?: string;
  state?: JobState;
  jobId?: string;
}

interface ScenarioApi {
  scenario: ScenarioContextValue | null;
  setScenario: (value: ScenarioContextValue | null) => void;
}

const ScenarioCtx = createContext<ScenarioApi | null>(null);

export function useScenarioContext(): ScenarioApi {
  const ctx = useContext(ScenarioCtx);
  if (!ctx) throw new Error('useScenarioContext must be used inside <ScenarioContextProvider>');
  return ctx;
}

/** Declare the top-bar scenario context for as long as this view is mounted. */
export function useScenarioContextEffect(value: ScenarioContextValue | null): void {
  const { setScenario } = useScenarioContext();
  const key = value ? JSON.stringify(value) : null;
  useEffect(() => {
    setScenario(key ? (JSON.parse(key) as ScenarioContextValue) : null);
    return () => setScenario(null);
  }, [key, setScenario]);
}

export function ScenarioContextProvider({ children }: { children: ReactNode }) {
  const [scenario, setScenarioState] = useState<ScenarioContextValue | null>(null);
  const setScenario = useCallback((v: ScenarioContextValue | null) => setScenarioState(v), []);
  const api = useMemo(() => ({ scenario, setScenario }), [scenario, setScenario]);
  return <ScenarioCtx.Provider value={api}>{children}</ScenarioCtx.Provider>;
}
