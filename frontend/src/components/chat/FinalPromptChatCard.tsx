import { useState } from "react";
import type { FinalPrompt } from "../../types";
import { copyToClipboard } from "../../utils/copyToClipboard";

const REVIEW_CHECKS: Array<[keyof FinalPrompt["review"], string]> = [
  ["is_clear", "Clear"],
  ["uses_only_known_details", "No invented details"],
  ["is_xml_valid", "Valid XML"],
  ["no_missing_critical_info", "Complete"],
  ["ready_to_return", "Ready"],
];

function formatPromptSize(text: string): string {
  const bytes = new TextEncoder().encode(text).length;
  return bytes >= 1024 ? `${(bytes / 1024).toFixed(1)} KB` : `${bytes} B`;
}

function parseXMLSections(xml: string): Array<{ tag: string; content: string }> {
  try {
    const doc = new DOMParser().parseFromString(xml, "text/xml");
    if (doc.querySelector("parsererror")) return [];
    return Array.from(doc.documentElement.children).map((el) => ({
      tag: el.tagName,
      content: el.textContent?.trim() ?? "",
    }));
  } catch {
    return [];
  }
}

function XMLSection({ tag, content }: { tag: string; content: string }) {
  const lines = content.split("\n").map((l) => l.trim()).filter(Boolean);
  const isList = lines.length > 1;

  return (
    <section className="space-y-1.5">
      <div>
        <span className="font-mono text-sm font-bold text-[#8c7357]">&lt;{tag}&gt;</span>
      </div>
      <div className="border-l border-[#4e453d] pl-4">
        {isList ? (
          <ul className="list-disc list-inside space-y-1 text-[#d1c4b9]">
            {lines.map((line, i) => (
              <li key={i} className="font-mono text-sm leading-relaxed">
                {line.replace(/^[-•*]\s*/, "")}
              </li>
            ))}
          </ul>
        ) : (
          <p className="font-mono text-sm leading-relaxed text-[#d1c4b9]">{content}</p>
        )}
      </div>
      <div>
        <span className="font-mono text-sm font-bold text-[#8c7357]">&lt;/{tag}&gt;</span>
      </div>
    </section>
  );
}

export function FinalPromptChatCard({ finalPrompt }: { finalPrompt: FinalPrompt }) {
  const [copied, setCopied] = useState(false);
  const { review } = finalPrompt;
  const sections = parseXMLSections(finalPrompt.prompt);
  const allPassed = REVIEW_CHECKS.every(([key]) => Boolean(review[key]));
  const promptSize = formatPromptSize(finalPrompt.prompt);

  async function handleCopy() {
    const ok = await copyToClipboard(finalPrompt.prompt);
    setCopied(ok);
    window.setTimeout(() => setCopied(false), 1800);
  }

  return (
    <div className="w-full overflow-hidden rounded-2xl border border-[#4e453d]/40 bg-[#151311] shadow-2xl">
      {/* Card header */}
      <div className="flex items-center justify-between px-5 py-3 bg-[#1e1b19]">
        <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[#9a8f84]">
          Final Prompt Architecture
        </h2>
        <div className="flex items-center gap-2">
          <span className="rounded border border-[#8c7357]/30 bg-[#8c7357]/10 px-2 py-0.5 text-[10px] font-bold uppercase text-[#a78c6f]">
            {allPassed ? "Optimized" : `${review.quality_score}/100`}
          </span>
          <span className="rounded bg-[#8c7357]/10 border border-[#8c7357]/20 px-2 py-0.5 text-[10px] font-bold text-[#8c7357]">
            {promptSize}
          </span>
        </div>
      </div>

      {/* Code editor window */}
      <div className="border-t border-[#4e453d]/40">
        {/* Window chrome */}
        <div className="flex items-center justify-between border-b border-[#383432] bg-[#1e1b19]/50 px-5 py-3">
          <div className="flex gap-1.5">
            <div className="h-2.5 w-2.5 rounded-full bg-[#383432]" />
            <div className="h-2.5 w-2.5 rounded-full bg-[#383432]" />
            <div className="h-2.5 w-2.5 rounded-full bg-[#383432]" />
          </div>
          <span className="font-mono text-[10px] text-[#9a8f84]">prompt_final.xml</span>
        </div>

        {/* XML content */}
        <div className="space-y-6 p-8 font-mono text-sm leading-relaxed text-[#d1c4b9]">
          {sections.length > 0 ? (
            sections.map(({ tag, content }) => (
              <XMLSection key={tag} tag={tag} content={content} />
            ))
          ) : (
            <pre className="whitespace-pre-wrap text-[#d1c4b9]">{finalPrompt.prompt}</pre>
          )}
        </div>
      </div>

      {/* Completion action bar */}
      <div className="border-t border-[#4e453d]/40 bg-[#151311]/80 p-6 backdrop-blur-md">
        <div className="flex items-center justify-between gap-4 rounded-2xl border border-[#8c7357]/20 bg-[#8c7357]/5 p-4 shadow-xl backdrop-blur-sm">
          <div className="flex items-center gap-4 px-2">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#8c7357]/10 text-[#8c7357]">
              <span className="material-symbols-outlined" style={{ fontSize: "20px" }}>check_circle</span>
            </div>
            <div>
              <p className="text-sm font-semibold text-[#e8e1dd]">Prompt Generation Complete</p>
              <p className="text-xs text-[#9a8f84]">Quality score {review.quality_score}/100</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleCopy}
            className="flex shrink-0 items-center gap-2 rounded-xl bg-[#8c7357] px-6 py-2.5 text-sm font-bold text-[#3f2d16] shadow-lg shadow-[#8c7357]/20 transition-all hover:bg-[#a78c6f] active:scale-95"
          >
            <span className="material-symbols-outlined" style={{ fontSize: "18px" }}>content_copy</span>
            <span>{copied ? "Copied!" : "Copy Prompt"}</span>
          </button>
        </div>
      </div>

      {/* Review checks */}
      <div className="flex flex-wrap gap-2 border-t border-[#4e453d]/40 bg-[#1e1b19] px-5 py-4">
        {REVIEW_CHECKS.map(([key, label]) => {
          const passed = Boolean(review[key]);
          return (
            <span
              key={key}
              className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[11px] font-medium tracking-wide ${
                passed
                  ? "border-[#8c7357]/30 bg-[#8c7357]/10 text-[#a78c6f]"
                  : "border-[#4e453d] bg-[#1e1b19] text-[#9a8f84]"
              }`}
            >
              <span className="material-symbols-outlined" style={{ fontSize: "13px" }}>
                {passed ? "check_circle" : "cancel"}
              </span>
              {label}
            </span>
          );
        })}
      </div>

      {/* Missing / fixes — only shown when present */}
      {(review.missing_or_unclear_items.length > 0 || review.fixes_applied.length > 0) && (
        <div className="space-y-2 border-t border-[#4e453d]/40 bg-[#1e1b19] px-5 py-3">
          {review.missing_or_unclear_items.length > 0 && (
            <p className="text-xs text-amber-300">
              Missing or unclear: {review.missing_or_unclear_items.join(" · ")}
            </p>
          )}
          {review.fixes_applied.length > 0 && (
            <p className="text-xs text-[#9a8f84]">
              Fixes applied: {review.fixes_applied.join(" · ")}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
