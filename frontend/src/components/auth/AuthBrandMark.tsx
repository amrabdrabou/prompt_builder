interface AuthBrandMarkProps {
  compact?: boolean;
}

export function AuthBrandMark({ compact = false }: AuthBrandMarkProps) {
  return (
    <div className="flex items-center gap-2">
      <div
        className={`flex shrink-0 items-center justify-center rounded-lg bg-[#a78c6f] font-bold text-[#382610] ${
          compact ? "h-12 w-12 text-lg" : "h-8 w-8 text-sm"
        }`}
        aria-hidden="true"
      >
        PA
      </div>
      {!compact && (
        <span className="text-xl font-semibold tracking-normal text-[#e8e1dd]">
          Prompt Architect
        </span>
      )}
    </div>
  );
}
