import type { ReactNode } from "react";

interface BadgeProps {
  children: ReactNode;
  tone?: "gray" | "blue" | "green" | "amber";
}

const tones = {
  gray: "bg-surface-2 text-ink-subtle ring-1 ring-hairline",
  blue: "bg-accent-500/12 text-accent-100 ring-1 ring-accent-500/25",
  green: "bg-emerald-500/10 text-emerald-300 ring-1 ring-emerald-500/20",
  amber: "bg-amber-500/10 text-amber-200 ring-1 ring-amber-500/20",
};

export function Badge({ children, tone = "gray" }: BadgeProps) {
  return (
    <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${tones[tone]}`}>
      {children}
    </span>
  );
}
