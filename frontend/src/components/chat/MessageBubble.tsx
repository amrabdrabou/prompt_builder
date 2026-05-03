import type { ChatMessage } from "../../types";
import { LoadingDots } from "../ui/LoadingDots";
import { SuggestionsRow } from "./SuggestionsRow";
import { FinalPromptChatCard } from "./FinalPromptChatCard";

interface MessageBubbleProps {
  message: ChatMessage;
  disabled?: boolean;
  onSuggestionSelect: (suggestion: string) => void;
}

export function MessageBubble({ message, disabled = false, onSuggestionSelect }: MessageBubbleProps) {
  if (message.finalPrompt) {
    return (
      <div className="flex flex-col gap-3">
        <FinalPromptChatCard finalPrompt={message.finalPrompt} />
      </div>
    );
  }

  const isUser = message.role === "user";

  return (
    <div className={`flex gap-6 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#a78c6f] text-sm font-black text-[#382610]">
          PA
        </div>
      )}

      <div className={`flex max-w-[min(100%,42rem)] flex-col gap-3 ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`rounded-2xl border p-5 text-sm leading-6 ${
            isUser
              ? "rounded-tr-none border-[#e0c1a1]/10 bg-[#e0c1a1]/5 text-[#e8e1dd]"
              : "rounded-tl-none border-stone-800/30 bg-[#1e1b19] text-stone-300"
          }`}
        >
          {message.content ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <span className="text-stone-500">
              <LoadingDots />
            </span>
          )}
        </div>

        {message.suggestions && message.suggestions.length > 0 && (
          <SuggestionsRow
            suggestions={message.suggestions}
            disabled={disabled}
            onSelect={onSuggestionSelect}
          />
        )}
      </div>

      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-stone-800 text-xs font-bold text-stone-300">
          You
        </div>
      )}
    </div>
  );
}
