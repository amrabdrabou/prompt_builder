import { useState } from "react";

interface ConversationComposerProps {
  disabled?: boolean;
  onLazyGenerate: () => void;
  onSend: (message: string) => void;
}

export function ConversationComposer({
  disabled = false,
  onLazyGenerate,
  onSend,
}: ConversationComposerProps) {
  const [value, setValue] = useState("");

  function submit() {
    const message = value.trim();
    if (!message || disabled) {
      return;
    }

    setValue("");
    onSend(message);
  }

  return (
    <div className="mt-auto border-t border-[#4e453d]/20 bg-[#151311]/80 p-6 backdrop-blur-md">
      <div className="mx-auto max-w-[800px]">
        <div className="overflow-hidden rounded-2xl border border-stone-800 bg-[#2d2927] shadow-2xl transition focus-within:border-[#8c7357]/60 focus-within:ring-1 focus-within:ring-[#8c7357]/20">
          <textarea
            value={value}
            onChange={(event) => setValue(event.target.value)}
            onKeyDown={(event) => {
              if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
                event.preventDefault();
                submit();
              }
            }}
            disabled={disabled}
            className="max-h-48 min-h-12 w-full resize-none border-none bg-transparent px-5 py-4 text-sm leading-6 text-[#e8e1dd] outline-none placeholder:text-stone-500 focus:ring-0"
            placeholder="Answer the question or refine the prompt logic..."
            rows={2}
          />
          <div className="flex flex-col gap-3 border-t border-stone-800/60 bg-stone-900/40 p-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="text-[10px] font-medium uppercase tracking-[0.2em] text-stone-600">
              Prompt Architect Engine v2.4
            </div>
            <div className="flex items-center justify-end gap-3">
              <button
                className="px-4 py-2 text-xs font-bold uppercase tracking-widest text-stone-400 transition hover:text-stone-200 focus:outline-none focus:ring-2 focus:ring-[#8c7357]/40 disabled:cursor-not-allowed disabled:opacity-50"
                disabled={disabled}
                onClick={onLazyGenerate}
                type="button"
              >
                Generate Lazy Prompt
              </button>
              <button
                className="flex min-h-10 items-center gap-2 rounded-xl bg-[#8c7357] px-5 py-2 text-sm font-semibold text-[#3f2d16] shadow-lg shadow-[#8c7357]/10 transition hover:bg-[#a78c6f] focus:outline-none focus:ring-2 focus:ring-[#e0c1a1]/50 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
                disabled={disabled || !value.trim()}
                onClick={submit}
                type="button"
              >
                Send Update
                <span aria-hidden="true">-&gt;</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
