import type { ButtonHTMLAttributes, ReactNode } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: "primary" | "secondary" | "ghost";
}

const variants = {
  primary: "bg-accent-600 text-white hover:bg-accent-700 disabled:bg-surface-3 disabled:text-ink-tertiary",
  secondary: "bg-surface-1 text-ink ring-1 ring-hairline hover:bg-surface-2",
  ghost: "bg-transparent text-ink-muted hover:bg-surface-2 hover:text-ink",
};

export function Button({
  children,
  className = "",
  variant = "primary",
  ...props
}: ButtonProps) {
  return (
    <button
      className={`inline-flex min-h-11 items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-accent-500/70 focus:ring-offset-2 focus:ring-offset-canvas ${variants[variant]} disabled:cursor-not-allowed disabled:shadow-none ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
