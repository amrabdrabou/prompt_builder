import type { PromptType } from "../../types";
import { formatPromptType } from "../../utils/formatters";

const promptTypes: PromptType[] = [
  "writing",
  "coding",
  "marketing",
  "analysis",
  "research",
  "planning",
  "image_generation",
  "automation",
  "other",
];

interface StartPromptTypePickerProps {
  disabled?: boolean;
  selectedType: PromptType;
  onSelect: (type: PromptType) => void;
}

export function StartPromptTypePicker({
  disabled = false,
  selectedType,
  onSelect,
}: StartPromptTypePickerProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-[10px] font-bold uppercase tracking-[0.24em] text-[#9a8f84]">
          Prompt type
        </p>
        <p className="hidden text-xs text-[#d1c4b9] sm:block">
          Choose the closest category before generating.
        </p>
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
        {promptTypes.map((type) => {
          const isSelected = selectedType === type;

          return (
            <button
              key={type}
              className={`min-h-10 rounded-lg border px-3 py-2 text-xs font-semibold capitalize transition focus:outline-none focus:ring-2 focus:ring-[#e0c1a1]/50 disabled:cursor-not-allowed disabled:opacity-50 ${
                isSelected
                  ? "border-[#e0c1a1]/60 bg-[#e0c1a1]/15 text-[#e0c1a1]"
                  : "border-[#4e453d]/40 bg-[#1e1b19]/70 text-[#d1c4b9] hover:border-[#e0c1a1]/40 hover:text-[#e8e1dd]"
              }`}
              disabled={disabled}
              onClick={() => onSelect(type)}
              type="button"
            >
              {formatPromptType(type)}
            </button>
          );
        })}
      </div>
    </div>
  );
}
