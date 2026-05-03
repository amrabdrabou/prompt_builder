import type { ConversationState } from "../../types";
import { formatPromptType } from "../../utils/formatters";

function readinessScore(state: ConversationState): number {
  if (state.ready_to_finalize) {
    return 100;
  }

  const scores = Object.values(state.confidence);
  const average = scores.reduce((sum, score) => sum + score, 0) / scores.length;
  return Math.round(average);
}

interface StatTileProps {
  label: string;
  value: string;
}

function StatTile({ label, value }: StatTileProps) {
  return (
    <div className="rounded-xl border border-stone-800/60 bg-stone-950 p-3">
      <span className="mb-1 block text-[10px] font-bold uppercase tracking-wide text-stone-500">
        {label}
      </span>
      <p className="truncate text-sm font-medium capitalize text-stone-200">{value || "Unknown"}</p>
    </div>
  );
}

export function ConversationIntelligencePanel({ state }: { state: ConversationState }) {
  const score = readinessScore(state);
  const missingFields = state.missing_fields.length > 0 ? state.missing_fields : ["No critical gaps"];

  return (
    <section className="hidden h-fit w-[400px] shrink-0 rounded-2xl border border-[#4e453d]/20 bg-[#1e1b19] shadow-sm 2xl:block">
      <div className="space-y-8 p-6">
        <div>
          <h2 className="text-xl font-semibold leading-7 text-stone-200">Intelligence Hub</h2>
          <p className="mt-1 text-sm leading-5 text-stone-500">
            Enhance the prompt logic before generation.
          </p>
        </div>

        <div className="space-y-4">
          <div className="flex items-end justify-between gap-3">
            <h3 className="text-xs font-bold uppercase tracking-widest text-stone-400">
              State Evaluation
            </h3>
            <span className="text-xs font-medium text-[#e0c1a1]">{score}% Ready</span>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <StatTile label="Type" value={formatPromptType(state.prompt_type)} />
            <StatTile label="Goal" value={state.goal ? "Known" : "Missing"} />
            <StatTile label="Output" value={state.output_format ? "Known" : "Missing"} />
          </div>

          <div className="h-2 rounded-full bg-stone-900">
            <div
              className="h-2 rounded-full bg-[#e0c1a1] transition-all"
              style={{ width: `${score}%` }}
            />
          </div>
        </div>

        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-widest text-stone-400">
            Current Understanding
          </h3>
          <div className="space-y-2 text-sm leading-6 text-stone-400">
            <p>
              <span className="text-stone-500">Goal:</span>{" "}
              <span className="text-stone-300">{state.goal || "Waiting for a clearer goal."}</span>
            </p>
            <p>
              <span className="text-stone-500">Audience:</span>{" "}
              <span className="text-stone-300">{state.audience || "Not specified yet."}</span>
            </p>
          </div>
        </div>

        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-widest text-stone-400">
            Still Needed
          </h3>
          <div className="flex flex-wrap gap-2">
            {missingFields.map((field) => (
              <span
                key={field}
                className="rounded-full border border-[#52473b] bg-[#52473b]/30 px-3 py-1 text-xs text-[#d4c4b4]"
              >
                {field}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
