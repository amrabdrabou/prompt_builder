interface SuggestionsRowProps {
  suggestions: string[];
  disabled?: boolean;
  onSelect: (suggestion: string) => void;
}

export function SuggestionsRow({ suggestions, disabled = false, onSelect }: SuggestionsRowProps) {
  if (suggestions.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-2 pt-1">
      {suggestions.map((suggestion) => (
        <button
          key={suggestion}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(suggestion)}
          className="rounded-full border border-[#52473b] bg-[#52473b]/40 px-3 py-1.5 text-xs font-medium text-[#d4c4b4] transition hover:bg-[#52473b]/60 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {suggestion}
        </button>
      ))}
    </div>
  );
}
