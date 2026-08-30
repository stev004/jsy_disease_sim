export interface SegOption<T extends string> {
  value: T;
  label: string;
  title?: string;
}

export interface SegProps<T extends string> {
  options: SegOption<T>[];
  value: T;
  onChange: (value: T) => void;
  /** aria-label for the group. */
  label: string;
  title?: string;
  className?: string;
}

/** Segmented control: `.seg` with `aria-pressed` on the active button. */
export function Seg<T extends string>({
  options,
  value,
  onChange,
  label,
  title,
  className,
}: SegProps<T>) {
  return (
    <div
      className={['seg', className].filter(Boolean).join(' ')}
      role="group"
      aria-label={label}
      title={title}
    >
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          title={o.title}
          aria-pressed={value === o.value}
          onClick={() => onChange(o.value)}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
