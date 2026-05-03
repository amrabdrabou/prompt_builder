import { apiFetch } from "./client";
import type {
  Conversation,
  ConversationDetail,
  FinalPromptRecord,
  Message,
} from "../types";

export function listConversations(): Promise<Conversation[]> {
  return apiFetch<Conversation[]>("/conversations");
}

export function createConversation(): Promise<ConversationDetail> {
  return apiFetch<ConversationDetail>("/conversations", {
    method: "POST",
  });
}

export function getConversation(id: string): Promise<ConversationDetail> {
  return apiFetch<ConversationDetail>(`/conversations/${id}`);
}

export function getMessages(id: string): Promise<Message[]> {
  return apiFetch<Message[]>(`/conversations/${id}/messages`);
}

export function getFinalPrompts(id: string): Promise<FinalPromptRecord[]> {
  return apiFetch<FinalPromptRecord[]>(`/conversations/${id}/final-prompts`);
}
