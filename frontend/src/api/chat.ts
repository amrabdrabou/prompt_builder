import { API_BASE_URL, ApiError, RateLimitError } from "./client";
import type { ChatRequest, ChatSseEvent } from "../types";

type ChatEventHandler = (event: ChatSseEvent) => void;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function parseEvent(line: string): ChatSseEvent | null {
  if (!line.startsWith("data: ")) {
    return null;
  }

  const parsed: unknown = JSON.parse(line.slice(6));

  if (!isRecord(parsed) || typeof parsed.type !== "string") {
    return null;
  }

  return parsed as unknown as ChatSseEvent;
}

function emitBufferedEvents(buffer: string, onEvent: ChatEventHandler): string {
  const chunks = buffer.split("\n\n");
  const remainder = chunks.pop() ?? "";

  for (const chunk of chunks) {
    const line = chunk.split("\n").find((item) => item.startsWith("data: "));
    if (!line) {
      continue;
    }

    const event = parseEvent(line);
    if (event) {
      onEvent(event);
    }
  }

  return remainder;
}

export async function streamChat(
  request: ChatRequest,
  onEvent: ChatEventHandler,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
    signal,
  });

  if (!response.ok) {
    if (response.status === 429) {
      const retryAfter = response.headers.get("Retry-After");
      throw new RateLimitError(retryAfter ? parseInt(retryAfter, 10) : null);
    }
    throw new ApiError("The agent could not process this message.", response.status);
  }

  if (!response.body) {
    throw new ApiError("The chat stream could not be opened.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();

    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    buffer = emitBufferedEvents(buffer, onEvent);
  }

  buffer += decoder.decode();
  emitBufferedEvents(`${buffer}\n\n`, onEvent);
}
