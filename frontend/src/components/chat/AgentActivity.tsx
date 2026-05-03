import type { AgentActivityItem } from "../../types";

interface AgentActivityProps {
  items: AgentActivityItem[];
}

export function AgentActivity({ items }: AgentActivityProps) {
  const isThinking = items.length === 0;

  return (
    <div className={`flex w-full gap-6 items-start transition-opacity ${isThinking ? "opacity-60" : ""}`}>
      {/* Avatar */}
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-colors ${
          isThinking ? "bg-[#221f1d]" : "bg-[#8c7357]/10"
        }`}
      >
        <span
          className="material-symbols-outlined"
          style={{ fontSize: "18px", color: isThinking ? "#9a8f84" : "#8c7357" }}
        >
          auto_awesome
        </span>
      </div>

      {/* Thinking dots */}
      {isThinking && (
        <div className="flex gap-1.5 py-3">
          <span className="h-1.5 w-1.5 rounded-full bg-[#383432] animate-pulse" />
          <span className="h-1.5 w-1.5 rounded-full bg-[#383432] animate-pulse [animation-delay:150ms]" />
          <span className="h-1.5 w-1.5 rounded-full bg-[#383432] animate-pulse [animation-delay:300ms]" />
        </div>
      )}

      {/* Activity steps */}
      {!isThinking && (
        <div className="space-y-2.5 pb-1 pt-1.5">
          {items.map((item, index) => {
            const isLatest = index === items.length - 1;
            return (
              <div key={item.id} className="flex items-center gap-2.5">
                <span
                  className={`h-1.5 w-1.5 shrink-0 rounded-full transition-colors ${
                    isLatest
                      ? "bg-[#8c7357] shadow-[0_0_0_3px_rgba(140,115,87,0.15)]"
                      : "bg-[#4e453d]"
                  }`}
                />
                <span
                  className={`text-sm transition-colors ${
                    isLatest ? "text-[#d1c4b9]" : "text-[#9a8f84]"
                  }`}
                >
                  {item.message}
                </span>
                {isLatest && (
                  <span className="flex gap-1">
                    <span className="h-1 w-1 rounded-full bg-[#8c7357] animate-pulse" />
                    <span className="h-1 w-1 rounded-full bg-[#8c7357] animate-pulse [animation-delay:150ms]" />
                    <span className="h-1 w-1 rounded-full bg-[#8c7357] animate-pulse [animation-delay:300ms]" />
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
