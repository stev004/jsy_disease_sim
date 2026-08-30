import type { HTMLAttributes, ReactNode } from 'react';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children?: ReactNode;
}

/** Raised panel: `.card` (panel background, hairline border, soft shadow). */
export function Card({ className, children, ...rest }: CardProps) {
  return (
    <div className={['card', className].filter(Boolean).join(' ')} {...rest}>
      {children}
    </div>
  );
}
