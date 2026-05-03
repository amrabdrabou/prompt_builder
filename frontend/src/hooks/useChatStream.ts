import { useCallback, useEffect, useRef, useState } from "react";
import { streamChat } from "../api/chat";
import { RateLimitError } from "../api/client";
import type {
  AgentActivityItem,
  AssistantStatus,
  ChatMessage,
  ConversationState,
  FinalPrompt,
} from "../types";

const emptyState: ConversationState = {
  title: "",
  prompt_type: "other",
  goal: "",
  audience: "",
  constraints: [],
  output_format: "",
  confidence: {
    goal: 0,
    audience: 0,
    constraints: 0,
    output_format: 0,
  },
  missing_fields: [],
  ready_to_finalize: false,
};

function makeId(prefix: string): string {
  return `${prefix}-${crypto.randomUUID()}`;
}

export function useChatStream(onConversationCreated?: (conversationId: string) => void) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationState, setConversationState] = useState<ConversationState>(emptyState);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [finalPrompt, setFinalPrompt] = useState<FinalPrompt | null>(null);
  const [status, setStatus] = useState<AssistantStatus>("ready");
  const [activity, setActivity] = useState<AgentActivityItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Cancel any in-flight request when the hook unmounts.
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setConversationState(emptyState);
    setConversationId(undefined);
    setFinalPrompt(null);
    setStatus("ready");
    setActivity([]);
    setError(null);
  }, []);

  const hydrate = useCallback((
    nextConversationId: string,
    nextMessages: ChatMessage[],
    nextState: ConversationState,
    nextFinalPrompt: FinalPrompt | null,
  ) => {
    abortRef.current?.abort();
    setConversationId(nextConversationId);

    // Attach finalPrompt to the last assistant message so it renders inline.
    let messagesWithMeta = nextMessages;
    if (nextFinalPrompt) {
      const lastAssistantIdx = nextMessages.reduceRight(
        (found, m, i) => (found === -1 && m.role === "assistant" ? i : found),
        -1,
      );
      if (lastAssistantIdx >= 0) {
        messagesWithMeta = nextMessages.map((m, i) =>
          i === lastAssistantIdx ? { ...m, finalPrompt: nextFinalPrompt } : m,
        );
      }
    }

    setMessages(messagesWithMeta);
    setConversationState(nextState);
    setFinalPrompt(nextFinalPrompt);
    setStatus(nextFinalPrompt ? "final" : "ready");
    setActivity([]);
    setError(null);
  }, []);

  const sendMessage = useCallback(async (message: string, targetConversationId?: string) => {
    const userMessage: ChatMessage = {
      id: makeId("user"),
      role: "user",
      content: message,
    };
    const assistantId = makeId("assistant");
    const assistantMessage: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      streaming: true,
    };

    setMessages((current) => [...current, userMessage, assistantMessage]);
    setFinalPrompt(null);
    setActivity([]);
    setError(null);
    setStatus("thinking");

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await streamChat(
        {
          user_message: message,
          conversation_id: targetConversationId ?? conversationId,
        },
        (event) => {
          if (event.type === "status") {
            setStatus((current) => (current === "asking" ? "asking" : "thinking"));
            setActivity((current) => {
              if (current.some((item) => item.message === event.message)) {
                return current;
              }
              return [...current, { id: makeId("activity"), message: event.message }];
            });
          }

          if (event.type === "text_delta") {
            setStatus("asking");
            setMessages((current) =>
              current.map((item) =>
                item.id === assistantId
                  ? { ...item, content: `${item.content}${event.text}` }
                  : item,
              ),
            );
          }

          if (event.type === "ask_question") {
            setConversationId(event.conversation_id);
            onConversationCreated?.(event.conversation_id);
            setConversationState(event.conversation_state);
            setStatus("ready");
            setMessages((current) =>
              current.map((item) =>
                item.id === assistantId
                  ? {
                      ...item,
                      content: event.message,
                      streaming: false,
                      suggestions: event.suggestions,
                      conversationState: event.conversation_state,
                    }
                  : item,
              ),
            );
          }

          if (event.type === "final_prompt") {
            setConversationId(event.conversation_id);
            onConversationCreated?.(event.conversation_id);
            setConversationState(event.conversation_state);
            const fp: FinalPrompt = {
              id: event.prompt_id,
              conversation_id: event.conversation_id,
              prompt: event.prompt,
              review: event.prompt_review,
            };
            setFinalPrompt(fp);
            setStatus("final");
            setMessages((current) =>
              current.map((item) =>
                item.id === assistantId
                  ? { ...item, content: "", streaming: false, finalPrompt: fp }
                  : item,
              ),
            );
          }

          if (event.type === "error") {
            setStatus("error");
            setActivity([]);
            setError("Something went wrong while building the prompt. Please try again.");
          }
        },
        controller.signal,
      );
    } catch (err) {
      setStatus("error");
      setActivity([]);
      if (err instanceof RateLimitError) {
        const msg = err.retryAfterSeconds
          ? `Too many requests. Please try again in ${err.retryAfterSeconds} seconds.`
          : "Too many requests. Please try again shortly.";
        setError(msg);
      } else {
        setError("The agent could not respond. Check your sign-in status and try again.");
      }
      setMessages((current) => current.filter((item) => item.id !== assistantId));
    }
  }, [conversationId, onConversationCreated]);

  const reportError = useCallback((message: string) => {
    setError(message);
  }, []);

  return {
    messages,
    conversationId,
    conversationState,
    finalPrompt,
    status,
    activity,
    error,
    sendMessage,
    reset,
    hydrate,
    reportError,
  };
}
