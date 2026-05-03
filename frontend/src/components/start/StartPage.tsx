import { useState } from "react";
import type { PromptType } from "../../types";
import { StartPromptInput } from "./StartPromptInput";
import { StartPromptTypePicker } from "./StartPromptTypePicker";
import { StartStatusBar } from "./StartStatusBar";
import { StartSuggestionGrid } from "./StartSuggestionGrid";

interface StartPageProps {
  disabled?: boolean;
  error: string | null;
  onSend: (message: string) => void;
}

export function StartPage({ disabled = false, error, onSend }: StartPageProps) {
  const [promptType, setPromptType] = useState<PromptType>("coding");

  return (
    <section className="workspace-grid relative flex min-h-full flex-1 items-center justify-center overflow-hidden bg-[#151311] p-5 md:p-10 lg:p-16">
      <section className="relative z-10 w-full max-w-4xl space-y-10">
        <div className="space-y-2 text-center">
          <h1 className="text-4xl font-bold leading-tight tracking-normal text-[#e8e1dd] md:text-5xl">
            What will we <span className="italic text-[#e0c1a1]">discover</span> today?
          </h1>
          <p className="text-xs font-medium uppercase tracking-[0.3em] text-[#9a8f84]">
            Initialize prompt architecture
          </p>
        </div>

        <StartPromptTypePicker
          disabled={disabled}
          selectedType={promptType}
          onSelect={setPromptType}
        />

        <StartPromptInput disabled={disabled} promptType={promptType} onSend={onSend} />

        {error && (
          <div className="rounded-lg border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
            {error}
          </div>
        )}

        <StartSuggestionGrid disabled={disabled} promptType={promptType} onSelect={onSend} />
      </section>
      <StartStatusBar />
    </section>
  );
}
