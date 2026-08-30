import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

export type Theme = 'light' | 'dark';
/** `null` = follow the OS (`prefers-color-scheme`). */
export type ThemeSetting = Theme | null;

interface ThemeApi {
  /** The explicit choice, or null while following the system. */
  setting: ThemeSetting;
  /** The theme actually in effect. */
  theme: Theme;
  setTheme: (setting: ThemeSetting) => void;
  toggleTheme: () => void;
}

const STORAGE_KEY = 'jos.theme';

const ThemeContext = createContext<ThemeApi | null>(null);

export function useTheme(): ThemeApi {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used inside <ThemeProvider>');
  return ctx;
}

function systemTheme(): Theme {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function readStored(): ThemeSetting {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    return v === 'dark' || v === 'light' ? v : null;
  } catch {
    return null;
  }
}

/** Sets `data-theme` on <html>; tokens.css handles the rest. */
export function ThemeProvider({ children }: { children: ReactNode }) {
  const [setting, setSetting] = useState<ThemeSetting>(readStored);
  const [system, setSystem] = useState<Theme>(systemTheme);

  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const onChange = () => setSystem(mq.matches ? 'dark' : 'light');
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    if (setting) root.setAttribute('data-theme', setting);
    else root.removeAttribute('data-theme');
    try {
      if (setting) localStorage.setItem(STORAGE_KEY, setting);
      else localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* storage unavailable */
    }
  }, [setting]);

  const theme: Theme = setting ?? system;

  const setTheme = useCallback((next: ThemeSetting) => setSetting(next), []);
  const toggleTheme = useCallback(
    () => setSetting((prev) => ((prev ?? systemTheme()) === 'dark' ? 'light' : 'dark')),
    [],
  );

  const api = useMemo(
    () => ({ setting, theme, setTheme, toggleTheme }),
    [setting, theme, setTheme, toggleTheme],
  );

  return <ThemeContext.Provider value={api}>{children}</ThemeContext.Provider>;
}
