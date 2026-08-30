import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

/** How much scientific detail the UI shows. */
export type DetailLevel = 'simple' | 'scientific';

interface DetailApi {
  detail: DetailLevel;
  /** Convenience: `detail === 'scientific'`. */
  sci: boolean;
  setDetail: (level: DetailLevel) => void;
}

const STORAGE_KEY = 'jos.detail';

const DetailContext = createContext<DetailApi | null>(null);

export function useDetail(): DetailApi {
  const ctx = useContext(DetailContext);
  if (!ctx) throw new Error('useDetail must be used inside <DetailProvider>');
  return ctx;
}

/**
 * Toggles `body.sci`, which reveals every `.sci-only` element (see base.css).
 * Components should prefer the CSS class over conditional rendering so the
 * switch stays instant and layout-stable.
 */
export function DetailProvider({ children }: { children: ReactNode }) {
  const [detail, setDetailState] = useState<DetailLevel>(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) === 'scientific' ? 'scientific' : 'simple';
    } catch {
      return 'simple';
    }
  });

  useEffect(() => {
    document.body.classList.toggle('sci', detail === 'scientific');
    try {
      localStorage.setItem(STORAGE_KEY, detail);
    } catch {
      /* storage unavailable */
    }
  }, [detail]);

  const setDetail = useCallback((level: DetailLevel) => setDetailState(level), []);
  const api = useMemo(
    () => ({ detail, sci: detail === 'scientific', setDetail }),
    [detail, setDetail],
  );

  return <DetailContext.Provider value={api}>{children}</DetailContext.Provider>;
}
