import type { ReactNode } from "react";
import { AuthBrandMark } from "./AuthBrandMark";

interface AuthCardProps {
  title: string;
  description: string;
  children: ReactNode;
}

export function AuthCard({ title, description, children }: AuthCardProps) {
  return (
    <section className="flex flex-1 flex-col items-center justify-center bg-[#151311] px-6 py-12 text-[#e8e1dd] md:px-16 lg:px-24 xl:px-32">
      <div className="flex w-full max-w-[400px] flex-col">
        <header className="mb-10 text-center md:text-left">
          <div className="mb-6 flex justify-center md:hidden">
            <AuthBrandMark compact />
          </div>
          <h1 className="mb-2 text-2xl font-semibold leading-8 tracking-normal text-[#e8e1dd]">
            {title}
          </h1>
          <p className="text-[15px] leading-6 text-[#9a8f84]">{description}</p>
        </header>

        <div className="flex flex-col gap-4">{children}</div>
      </div>
    </section>
  );
}
