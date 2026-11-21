// Small inline icons; decorative only (the visible text names each item).
type IconProps = { className?: string };

const common = {
  width: 20,
  height: 20,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
  focusable: false,
};

export function CasesIcon({ className }: IconProps) {
  return (
    <svg {...common} className={className}>
      <rect x="4" y="3.5" width="16" height="17" rx="2.5" />
      <path d="M8 8.5h8M8 12h8M8 15.5h5" />
    </svg>
  );
}

export function DataIcon({ className }: IconProps) {
  return (
    <svg {...common} className={className}>
      <ellipse cx="12" cy="6" rx="7" ry="2.8" />
      <path d="M5 6v6c0 1.6 3.1 2.8 7 2.8s7-1.2 7-2.8V6" />
      <path d="M5 12v6c0 1.6 3.1 2.8 7 2.8s7-1.2 7-2.8v-6" />
    </svg>
  );
}

export function MenuIcon({ className }: IconProps) {
  return (
    <svg {...common} className={className}>
      <path d="M4 7h16M4 12h16M4 17h16" />
    </svg>
  );
}

export function BrandMark({ className }: IconProps) {
  return (
    <svg
      width={32}
      height={32}
      viewBox="0 0 32 32"
      aria-hidden="true"
      focusable={false}
      className={className}
    >
      <rect width="32" height="32" rx="8" fill="#0f766e" />
      <path
        d="M16 8.5v15M8.5 16h15"
        stroke="#ffffff"
        strokeWidth="3.2"
        strokeLinecap="round"
      />
      <circle
        cx="16"
        cy="16"
        r="10.5"
        fill="none"
        stroke="#7ff0dd"
        strokeWidth="1.4"
        opacity="0.7"
      />
    </svg>
  );
}

export function ChevronIcon({ className }: IconProps) {
  return (
    <svg {...common} className={className}>
      <path d="M10 7l5 5-5 5" />
    </svg>
  );
}

export function CatalogueIcon({ className }: IconProps) {
  return (
    <svg {...common} className={className}>
      <rect x="3.5" y="4" width="17" height="16" rx="2.5" />
      <path d="M3.5 9h17M9 9v11" />
    </svg>
  );
}

export function ShortageIcon({ className }: IconProps) {
  return (
    <svg {...common} className={className}>
      <path d="M12 3.5 21 19.5H3z" />
      <path d="M12 10v4.5M12 17.2v.3" />
    </svg>
  );
}
