import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { Badge, PROVENANCE_MEANING } from '../components/Badge';
import { OSM_ATTRIBUTION } from '../map/geometry';

interface DrawerApi {
  open: boolean;
  openDrawer: () => void;
  closeDrawer: () => void;
  /** Replace the drawer body; pass null to restore the default content. */
  setDrawerContent: (content: ReactNode | null) => void;
}

const DrawerContext = createContext<DrawerApi | null>(null);

export function useDrawer(): DrawerApi {
  const ctx = useContext(DrawerContext);
  if (!ctx) throw new Error('useDrawer must be used inside <DrawerProvider>');
  return ctx;
}

/**
 * Right-side "Assumptions & sources" drawer: scrim, Esc to close, and a
 * replaceable body. Views that know a job's provenance can call
 * `setDrawerContent(...)`; otherwise the placeholder below is shown.
 */
export function DrawerProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [content, setContent] = useState<ReactNode | null>(null);

  const openDrawer = useCallback(() => setOpen(true), []);
  const closeDrawer = useCallback(() => setOpen(false), []);
  const setDrawerContent = useCallback((c: ReactNode | null) => setContent(c), []);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open]);

  const api = useMemo(
    () => ({ open, openDrawer, closeDrawer, setDrawerContent }),
    [open, openDrawer, closeDrawer, setDrawerContent],
  );

  return (
    <DrawerContext.Provider value={api}>
      {children}
      <div
        className={`scrim${open ? ' open' : ''}`}
        onClick={closeDrawer}
        aria-hidden="true"
      />
      <aside
        className={`drawer${open ? ' open' : ''}`}
        role="dialog"
        aria-label="Assumptions and sources"
        aria-hidden={!open}
      >
        <div className="dhead">
          <h1>Assumptions &amp; sources</h1>
          <button type="button" className="close-x" onClick={closeDrawer} aria-label="Close">
            ×
          </button>
        </div>
        <div className="body">{content ?? <DrawerPlaceholder />}</div>
      </aside>
    </DrawerContext.Provider>
  );
}

/**
 * Default drawer body: the permanent claim boundary, the provenance-label
 * legend and the map attribution. A results/compare view replaces this with
 * the live verification and hash panels via `setDrawerContent`.
 */
function DrawerPlaceholder() {
  return (
    <>
      <div className="dnote">
        This is a <b>synthetic research simulation</b> of a generated Jersey population. It is not a
        forecast, a surveillance product, or a policy recommendation. No real people are represented.
      </div>

      <div className="dsec">
        <h2>Verification</h2>
        <div className="dnote">
          Open a run to see its engine commit, request hash, scientific hashes and artifact
          verification status.
        </div>
      </div>

      <div className="dsec">
        <h2>What the labels mean</h2>
        <div className="kv">
          {(['observed', 'derived', 'literature', 'calibrated', 'assumption'] as const).map((k) => (
            <div className="li" key={k}>
              <span className="k">
                <Badge kind={k} />
              </span>
              <span className="v" style={{ fontWeight: 400, color: 'var(--ink-2)' }}>
                {PROVENANCE_MEANING[k]}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="dsec">
        <h2>Map</h2>
        <div className="dnote">{OSM_ATTRIBUTION}</div>
      </div>
    </>
  );
}
