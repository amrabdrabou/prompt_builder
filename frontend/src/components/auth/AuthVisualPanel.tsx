import { AuthBrandMark } from "./AuthBrandMark";

export function AuthVisualPanel() {
  return (
    <section className="relative hidden min-h-dvh w-1/2 flex-col justify-between overflow-hidden bg-[#100e0c] p-12 md:flex">
      <div className="auth-atmosphere absolute inset-0" aria-hidden="true" />
      <div className="auth-grid absolute inset-0 opacity-30" aria-hidden="true" />
      <div className="absolute inset-0 bg-gradient-to-t from-[#151311] via-transparent to-transparent" aria-hidden="true" />

      <div className="relative z-10">
        <AuthBrandMark />
      </div>

      <div className="relative z-10 mb-12 max-w-lg">
        <div className="mb-6 text-5xl font-black leading-none text-[#e0c1a1]/60" aria-hidden="true">
          "
        </div>
        <p className="mb-6 text-2xl font-semibold italic leading-snug tracking-normal text-[#e8e1dd]">
          Precision is not just about the words we choose, but the context we build around them.
          Every prompt is a blueprint for intelligence.
        </p>
        <div className="flex items-center gap-4">
          <div className="h-px w-8 bg-[#4e453d]" />
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-[#9a8f84]">
            Principles of Engineering
          </p>
        </div>
      </div>

      <p className="relative z-10 text-sm leading-5 text-[#9a8f84]">
        V.1 XML prompt builder with OpenAI Responses API
      </p>
    </section>
  );
}
