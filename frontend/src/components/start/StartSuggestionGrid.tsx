import type { PromptType } from "../../types";
import { formatPromptType } from "../../utils/formatters";

const suggestions = [
  {
    label: "Clarify",
    prompt:
      "Help me turn a rough idea into a clear prompt. Ask me the most important questions before writing the final prompt.",
  },
  {
    label: "Improve",
    prompt:
      "Help me improve an existing prompt. Focus on clarity, missing context, constraints, and output format.",
  },
  {
    label: "Finalize",
    prompt:
      "Help me create a polished final prompt from a clear goal. Keep only known details and return a structured result.",
  },
];

interface StartSuggestionGridProps {
  disabled?: boolean;
  promptType: PromptType;
  onSelect: (prompt: string) => void;
}

export function StartSuggestionGrid({
  disabled = false,
  promptType,
  onSelect,
}: StartSuggestionGridProps) {
  function selectPrompt(prompt: string) {
    onSelect(`Prompt type: ${formatPromptType(promptType)}\n\n${prompt}`);
  }

  return (
    <div className="grid gap-5 opacity-90 transition-opacity hover:opacity-100 md:grid-cols-3">
      {suggestions.map((suggestion) => (
        <button
          key={suggestion.label}
          className="workspace-glass workspace-scan-hover rounded-lg bg-[#1e1b19]/80 p-6 text-left transition hover:border-[#e0c1a1]/50 focus:outline-none focus:ring-2 focus:ring-[#e0c1a1]/50 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={disabled}
          onClick={() => selectPrompt(suggestion.prompt)}
          type="button"
        >
          <div className="mb-2 flex items-center gap-3">
            <span className="flex h-7 w-7 items-center justify-center rounded-md border border-[#e0c1a1]/30 text-xs font-bold text-[#e0c1a1]">
              {suggestion.label.slice(0, 1)}
            </span>
            <span className="text-[10px] font-bold uppercase tracking-widest text-[#9a8f84]">
              {suggestion.label}
            </span>
          </div>
          <p className="text-xs leading-relaxed text-[#d1c4b9]">{suggestion.prompt}</p>
        </button>
      ))}
    </div>
  );
}
