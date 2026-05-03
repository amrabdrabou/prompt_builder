import type { ReactNode } from "react";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-dvh flex-col bg-canvas text-ink xl:flex-row">
      {children}
    </div>
  );
}
