import { useEffect, useRef } from "react";
import type { AgentActivityItem, AssistantStatus, ChatMessage, ConversationState } from "../../types";
import { ConversationComposer } from "./ConversationComposer";
import { ConversationIntelligencePanel } from "./ConversationIntelligencePanel";
import { ConversationThread } from "./ConversationThread";
import { StartPage } from "../start/StartPage";

interface ChatWorkspaceProps {
  messages: ChatMessage[];
  status: AssistantStatus;
  activity: AgentActivityItem[];
  conversationState: ConversationState;
  conversationReady: boolean;
  error: string | null;
  onSend: (message: string) => void;
}

const lazyPromptRequest = (
  "Generate the final prompt now using the information already available. " +
  "If something is missing, keep the prompt minimal and do not invent specific facts."
);

export function ChatWorkspace({
  messages,
  status,
  activity,
  conversationState,
  conversationReady,
  error,
  onSend,
}: ChatWorkspaceProps) {
  const isBusy = status === "thinking" || status === "asking";
  const bottomRef = useRef<HTMLDivElement>(null);
  const isFinal = status === "final";

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  return (
    <main className="flex min-h-0 flex-1 flex-col bg-[#151311]">
      {messages.length === 0 || !conversationReady ? (
        <StartPage disabled={isBusy} error={error} onSend={onSend} />
      ) : (
        <div className="flex min-h-0 flex-1 gap-4 overflow-hidden p-4">
          <ConversationIntelligencePanel state={conversationState} />
          <section className="relative flex min-w-0 flex-1 flex-col overflow-hidden rounded-2xl border border-[#4e453d]/20 bg-[#151311] shadow-sm">
            <ConversationThread
              activity={activity}
              disabled={isBusy}
              error={error}
              messages={messages}
              status={status}
              onSuggestionSelect={onSend}
            />
            <div ref={bottomRef} />
            {!isFinal && (
              <ConversationComposer
                disabled={isBusy}
                onLazyGenerate={() => onSend(lazyPromptRequest)}
                onSend={onSend}
              />
            )}
          </section>
        </div>
      )}
    </main>
  );
}
