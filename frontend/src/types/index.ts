export type PromptType =
  | "writing"
  | "coding"
  | "marketing"
  | "analysis"
  | "research"
  | "planning"
  | "image_generation"
  | "automation"
  | "other";

export type MessageRole = "user" | "assistant";

export interface ConfidenceState {
  goal: number;
  audience: number;
  constraints: number;
  output_format: number;
}

export interface ConversationState {
  title: string;
  prompt_type: PromptType;
  goal: string;
  audience: string;
  constraints: string[];
  output_format: string;
  confidence: ConfidenceState;
  missing_fields: string[];
  ready_to_finalize: boolean;
}

export interface PromptReview {
  is_clear: boolean;
  uses_only_known_details: boolean;
  is_xml_valid: boolean;
  no_missing_critical_info: boolean;
  ready_to_return: boolean;
  quality_score: number;
  missing_or_unclear_items: string[];
  fixes_applied: string[];
}

export interface Conversation {
  id: string;
  title: string;
  prompt_type: PromptType;
  ready_to_finalize: boolean;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends Conversation {
  conversation_state: ConversationState;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  streaming?: boolean;
  suggestions?: string[];
  conversationState?: ConversationState;
  finalPrompt?: FinalPrompt;
}

export interface ChatRequest {
  user_message: string;
  conversation_id?: string;
}

export interface AskQuestionEvent {
  type: "ask_question";
  action: "ask_question";
  conversation_id: string;
  message: string;
  suggestions: string[];
  conversation_state: ConversationState;
}

export interface FinalPromptEvent {
  type: "final_prompt";
  action: "final_prompt";
  conversation_id: string;
  prompt_id: string;
  prompt: string;
  conversation_state: ConversationState;
  prompt_review: PromptReview;
}

export interface TextDeltaEvent {
  type: "text_delta";
  text: string;
}

export interface StatusEvent {
  type: "status";
  message: string;
}

export interface ErrorEvent {
  type: "error";
  detail: string;
}

export type ChatSseEvent =
  | StatusEvent
  | TextDeltaEvent
  | AskQuestionEvent
  | FinalPromptEvent
  | ErrorEvent;

export interface AgentActivityItem {
  id: string;
  message: string;
}

export interface FinalPrompt {
  id: string;
  conversation_id: string;
  prompt: string;
  prompt_type?: PromptType;
  quality_score?: number;
  review: PromptReview;
  created_at?: string;
}

export interface FinalPromptRecord {
  id: string;
  conversation_id: string;
  prompt: string;
  prompt_type: PromptType;
  quality_score: number;
  review: PromptReview;
  created_at: string;
}

export type AssistantStatus =
  | "ready"
  | "thinking"
  | "asking"
  | "final"
  | "error";

export interface User {
  id: string;
  email: string;
  name: string | null;
  picture_url: string | null;
  created_at: string;
}
