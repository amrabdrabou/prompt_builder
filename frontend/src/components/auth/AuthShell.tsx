import type { ReactNode } from "react";
import { AuthVisualPanel } from "./AuthVisualPanel";

interface AuthShellProps {
  children: ReactNode;
}

export function AuthShell({ children }: AuthShellProps) {
  return (
    <main className="flex min-h-dvh flex-col bg-[#151311] text-[#e8e1dd] md:flex-row">
      <AuthVisualPanel />
      {children}
    </main>
  );
}
