import type { ReactNode } from 'react';

/** Small uppercase section label (`.label`). */
export function Label({
  children,
  className,
  style,
  htmlFor,
}: {
  children: ReactNode;
  className?: string;
  style?: React.CSSProperties;
  htmlFor?: string;
}) {
  const cls = ['label', className].filter(Boolean).join(' ');
  if (htmlFor) {
    return (
      <label className={cls} style={style} htmlFor={htmlFor}>
        {children}
      </label>
    );
  }
  return (
    <div className={cls} style={style}>
      {children}
    </div>
  );
}
