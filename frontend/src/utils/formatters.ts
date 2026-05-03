import type { PromptType } from "../types";

export function formatPromptType(type: PromptType): string {
  return type.replace("_", " ");
}
