/**
 * Keyboard-shortcuts overlay (`?`).
 *
 * Mounted once by the app shell. It opens on a bare `?` keypress — never while
 * the user is typing in a field — or on a `jos:shortcuts` window event, which
 * the results workspace dispatches from its help affordance. Esc or the scrim
 * closes it.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import './drawer.css';

/** Event any view can dispatch to open this overlay. */
export const SHORTCUTS_EVENT = 'jos:shortcuts';

const ROWS: Array<[React.ReactNode, string]> = [
  [<kbd key="space">Space</kbd>, 'Play / pause the timeline'],
  [
    <span key="arrows">
      <kbd>←</kbd> <kbd>→</kbd>
    </span>,
    'Step one day',
  ],
  [<kbd key="esc">Esc</kbd>, 'Close panels and menus'],
  [<kbd key="q">?</kbd>, 'Show this help'],
];

function isTyping(target: EventTarget | null): boolean {
  const el = target as HTMLElement | null;
  if (!el || !el.tagName) return false;
  const tag = el.tagName.toUpperCase();
  return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || el.isContentEditable;
}

export function ShortcutsOverlay() {
  const [open, setOpen] = useState(false);
  const closeRef = useRef<HTMLButtonElement | null>(null);

  const close = useCallback(() => setOpen(false), []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setOpen((v) => (v ? false : v));
        return;
      }
      if (e.key !== '?' || isTyping(e.target)) return;
      e.preventDefault();
      setOpen((v) => !v);
    };
    const onEvent = () => setOpen(true);
    document.addEventListener('keydown', onKey);
    window.addEventListener(SHORTCUTS_EVENT, onEvent);
    return () => {
      document.removeEventListener('keydown', onKey);
      window.removeEventListener(SHORTCUTS_EVENT, onEvent);
    };
  }, []);

  useEffect(() => {
    if (open) closeRef.current?.focus();
  }, [open]);

  return (
    <>
      <div
        className={`scrim ks-scrim${open ? ' open' : ''}`}
        onClick={close}
        aria-hidden="true"
      />
      <div
        className={`card ks${open ? ' open' : ''}`}
        role="dialog"
        aria-label="Keyboard shortcuts"
        aria-hidden={!open}
      >
        <div className="ks-head">
          <h2>Keyboard shortcuts</h2>
          <button
            type="button"
            className="close-x"
            onClick={close}
            aria-label="Close"
            ref={closeRef}
          >
            ×
          </button>
        </div>
        <div className="ks-rows">
          {ROWS.map(([keys, description]) => (
            <div className="ks-row" key={description}>
              <span>{keys}</span>
              <span>{description}</span>
            </div>
          ))}
        </div>
        <p className="ks-foot">
          Shortcuts work in the results workspace; typing in a field never triggers them.
        </p>
      </div>
    </>
  );
}
