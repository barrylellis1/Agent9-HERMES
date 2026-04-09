import React from 'react';

interface BrandLogoProps {
  /** Mark + wordmark (default) or mark only */
  variant?: 'full' | 'mark';
  /** Size of the mark in px — wordmark scales proportionally */
  size?: number;
  /** 'light' = white mark on dark bg (default); 'dark' = dark mark on light bg */
  scheme?: 'light' | 'dark';
  className?: string;
}

/**
 * Decision Studio — The Aperture mark.
 * Three concentric squares: outer frame ring, hollow middle, solid center.
 * Maps to: clarity, signal filtering, root cause focus.
 */
export const BrandLogo: React.FC<BrandLogoProps> = ({
  variant = 'full',
  size = 32,
  scheme = 'light',
  className = '',
}) => {
  const fill = scheme === 'light' ? 'white' : '#0f172a';
  const wordmarkColor = scheme === 'light' ? 'text-white' : 'text-slate-900';
  const fontSize = Math.round(size * 0.45);
  const gap = Math.round(size * 0.35);

  const mark = (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      style={{ flexShrink: 0 }}
    >
      {/* Outer ring + hollow middle — evenodd creates the frame */}
      <path
        d="M4 4 H36 V36 H4 V4 Z M12 12 V28 H28 V12 H12 Z"
        fill={fill}
        fillRule="evenodd"
      />
      {/* Center square — the focused signal */}
      <rect x="17" y="17" width="6" height="6" fill={fill} />
    </svg>
  );

  if (variant === 'mark') return <span className={className}>{mark}</span>;

  return (
    <span
      className={`inline-flex items-center ${className}`}
      style={{ gap }}
    >
      {mark}
      <span
        className={`font-semibold tracking-tight leading-none ${wordmarkColor}`}
        style={{ fontSize, fontFamily: "'Satoshi', system-ui, sans-serif" }}
      >
        Decision Studio
      </span>
    </span>
  );
};
