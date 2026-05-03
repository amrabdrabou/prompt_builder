import { useCallback, useEffect, useState } from "react";
import {
  getConversation,
  getFinalPrompts,
  getMessages,
  listConversations,
} from "../api/conversations";
import type { Conversation, ConversationDetail, FinalPromptRecord, Message } from "../types";

interface ConversationBundle {
  detail: ConversationDetail;
  messages: Message[];
  finalPrompt: FinalPromptRecord | null;
}

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setConversations(await listConversations());
    } catch {
      setError("Conversations could not be loaded. Sign in through the backend first.");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadConversation = useCallback(async (id: string): Promise<ConversationBundle> => {
    const [detail, messages, finalPrompts] = await Promise.all([
      getConversation(id),
      getMessages(id),
      getFinalPrompts(id),
    ]);

    return {
      detail,
      messages,
      finalPrompt: finalPrompts[0] ?? null,
    };
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return {
    conversations,
    loading,
    error,
    refresh,
    loadConversation,
  };
}
