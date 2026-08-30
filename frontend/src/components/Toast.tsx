import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';

export type ToastTone = 'good' | 'bad' | 'neutral' | 'accent';

export interface ToastAction {
  label: string;
  fn: () => void;
}

export interface ToastInput {
  title: string;
  body?: string;
  tone?: ToastTone;
  action?: ToastAction;
  /** ms before auto-dismiss; default 8000, 0 disables. */
  timeout?: number;
}

interface ToastItem extends ToastInput {
  id: number;
  hiding: boolean;
}

interface ToastApi {
  showToast: (input: ToastInput) => number;
  dismissToast: (id: number) => void;
}

const ToastContext = createContext<ToastApi | null>(null);

/** `useToast().showToast({ title, body, tone, action })`. */
export function useToast(): ToastApi {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used inside <ToastProvider>');
  return ctx;
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const nextId = useRef(1);

  const dismissToast = useCallback((id: number) => {
    setToasts((list) => list.map((t) => (t.id === id ? { ...t, hiding: true } : t)));
    window.setTimeout(() => {
      setToasts((list) => list.filter((t) => t.id !== id));
    }, 300);
  }, []);

  const showToast = useCallback(
    (input: ToastInput): number => {
      const id = nextId.current++;
      setToasts((list) => [...list, { ...input, id, hiding: false }]);
      const timeout = input.timeout ?? 8000;
      if (timeout > 0) window.setTimeout(() => dismissToast(id), timeout);
      return id;
    },
    [dismissToast],
  );

  const api = useMemo(() => ({ showToast, dismissToast }), [showToast, dismissToast]);

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="toast-stack">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`card toast ${t.tone ?? 'neutral'}${t.hiding ? ' hide' : ''}`}
            role="status"
          >
            <div className="tt">{t.title}</div>
            <button
              type="button"
              className="close-x tx"
              aria-label="Dismiss notification"
              onClick={() => dismissToast(t.id)}
            >
              ×
            </button>
            {t.body && <div className="tb">{t.body}</div>}
            {t.action && (
              <button
                type="button"
                className="btn ta"
                onClick={() => {
                  dismissToast(t.id);
                  t.action?.fn();
                }}
              >
                {t.action.label}
              </button>
            )}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
