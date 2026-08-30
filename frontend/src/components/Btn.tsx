import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { Link } from 'react-router-dom';

export type BtnVariant = 'default' | 'primary' | 'ghost' | 'danger';

export interface BtnProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: BtnVariant;
  /** `.btn.big` — full-width, larger padding. */
  big?: boolean;
  /** Render as a router link styled as a button. */
  to?: string;
  children?: ReactNode;
}

function classes(variant: BtnVariant, big: boolean, extra?: string): string {
  return [
    'btn',
    variant === 'default' ? null : variant,
    big ? 'big' : null,
    extra,
  ]
    .filter(Boolean)
    .join(' ');
}

export function Btn({
  variant = 'default',
  big = false,
  to,
  className,
  children,
  ...rest
}: BtnProps) {
  const cls = classes(variant, big, className);
  if (to) {
    return (
      <Link to={to} className={cls}>
        {children}
      </Link>
    );
  }
  return (
    <button type="button" className={cls} {...rest}>
      {children}
    </button>
  );
}
