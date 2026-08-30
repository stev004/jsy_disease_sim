import { useEffect, useId, useRef, useState } from 'react';

export interface ExportMenuProps {
  /** Called when "Chart as PNG" is chosen. */
  onPng: () => void;
  /** Called when "Data as CSV" is chosen. */
  onCsv: () => void;
  /** aria-label suffix, e.g. "epidemic curve". */
  label: string;
}

/**
 * The compact chart Export menu (`.exp-wrap` / `.exp-btn` / `.exp-menu`).
 * Closes on outside click, Escape, and after either action runs.
 */
export function ExportMenu({ onPng, onCsv, label }: ExportMenuProps) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLSpanElement | null>(null);
  const menuId = useId();

  useEffect(() => {
    if (!open) return undefined;
    const onDocClick = (e: MouseEvent): void => {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onDocClick);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDocClick);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  return (
    <span className="exp-wrap" ref={wrapRef}>
      <button
        type="button"
        className="btn ghost exp-btn"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={menuId}
        aria-label={`Export ${label}`}
        onClick={() => setOpen((v) => !v)}
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 4v10M8.5 10.5L12 14l3.5-3.5M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
        </svg>
        Export
      </button>
      <div className={`card exp-menu${open ? ' open' : ''}`} id={menuId} role="menu">
        <button
          type="button"
          role="menuitem"
          onClick={() => {
            setOpen(false);
            onPng();
          }}
        >
          Chart as PNG
        </button>
        <button
          type="button"
          role="menuitem"
          onClick={() => {
            setOpen(false);
            onCsv();
          }}
        >
          Data as CSV
        </button>
      </div>
    </span>
  );
}
