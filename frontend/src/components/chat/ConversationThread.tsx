import type { ChatMessage } from "../../types";
import { AgentActivity } from "./AgentActivity";
import { MessageBubble } from "./MessageBubble";
import type { AgentActivityItem, AssistantStatus } from "../../types";

interface ConversationThreadProps {
  activity: AgentActivityItem[];
  disabled?: boolean;
  error: string | null;
  messages: ChatMessage[];
  status: AssistantStatus;
  onSuggestionSelect: (suggestion: string) => void;
}

export function ConversationThread({
  activity,
  disabled = false,
  error,
  messages,
  status,
  onSuggestionSelect,
}: ConversationThreadProps) {
  const isBusy = status === "thinking" || status === "asking";

  return (
    <div className="flex-1 overflow-y-auto px-4 py-8">
      <div className="mx-auto max-w-[800px] space-y-6">
        {messages.map((message) => {
          if (message.role === "assistant" && message.streaming && !message.content) {
            return <AgentActivity key={message.id} items={activity} />;
          }

          return (
            <MessageBubble
              key={message.id}
              message={message}
              disabled={disabled || isBusy}
              onSuggestionSelect={onSuggestionSelect}
            />
          );
        })}

        {error && (
          <div className="rounded-lg border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
