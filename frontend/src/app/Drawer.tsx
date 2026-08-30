import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { ProvenanceContent } from '../views/drawer';

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
        <div className="body">{content ?? <ProvenanceContent />}</div>
      </aside>
    </DrawerContext.Provider>
  );
}
