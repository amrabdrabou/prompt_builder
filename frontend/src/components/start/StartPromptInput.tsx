import { useState } from "react";
import type { PromptType } from "../../types";
import { formatPromptType } from "../../utils/formatters";

interface StartPromptInputProps {
  disabled?: boolean;
  promptType: PromptType;
  onSend: (message: string) => void;
}

export function StartPromptInput({ disabled = false, promptType, onSend }: StartPromptInputProps) {
  const [value, setValue] = useState("");

  function submit() {
    const message = value.trim();
    if (!message || disabled) {
      return;
    }

    setValue("");
    onSend(`Prompt type: ${formatPromptType(promptType)}\n\n${message}`);
  }

  return (
    <div className="workspace-glass rounded-xl bg-[#221f1d]/80 p-4 shadow-2xl transition focus-within:ring-1 focus-within:ring-[#e0c1a1]/40">
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
        className="min-h-40 w-full resize-none border-none bg-transparent px-2 py-4 text-base leading-6 text-[#e8e1dd] outline-none placeholder:text-[#9a8f84]/60 focus:ring-0"
        placeholder={`Describe the ${formatPromptType(promptType).toLowerCase()} prompt you want to build...`}
      />
      <div className="flex items-center justify-end gap-4 border-t border-[#4e453d]/25 pt-4">
        <span className="hidden font-mono text-[10px] uppercase tracking-widest text-[#9a8f84] sm:inline">
          Ctrl + Enter to execute
        </span>
        <button
          className="flex min-h-10 items-center gap-2 rounded-lg bg-[#e0c1a1] px-6 py-2 text-sm font-semibold uppercase tracking-wide text-[#3f2d16] transition hover:brightness-110 focus:outline-none focus:ring-2 focus:ring-[#e0c1a1]/60 focus:ring-offset-2 focus:ring-offset-[#151311] active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={disabled || !value.trim()}
          onClick={submit}
          type="button"
        >
          Generate
          <span aria-hidden="true">+</span>
        </button>
      </div>
    </div>
  );
}
