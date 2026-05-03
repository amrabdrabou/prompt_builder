import type { Conversation, User } from "../../types";

interface SidebarProps {
  conversations: Conversation[];
  selectedConversationId?: string;
  loading: boolean;
  onSelect: (id: string) => void;
  onNew: () => void;
  user: User;
  authError?: string | null;
  onLogout: () => void;
}

export function Sidebar({
  conversations,
  selectedConversationId,
  loading,
  onSelect,
  onNew,
  user,
  authError,
  onLogout,
}: SidebarProps) {
  return (
    <aside className="hidden h-dvh w-72 shrink-0 flex-col gap-4 border-r border-[#4e453d]/30 bg-[#100e0c] py-8 xl:flex">
      <div className="mb-6 px-6">
        <h1 className="text-lg font-black tracking-normal text-[#e8e1dd]">Prompt Builder</h1>
        <p className="text-[10px] font-medium uppercase tracking-[0.2em] text-[#9a8f84]">
          v2.4.0-alpha
        </p>
      </div>

      <div className="mb-4 px-6">
        <button
          className="flex min-h-11 w-full items-center justify-center gap-2 rounded-lg border border-[#e0c1a1]/30 bg-[#e0c1a1]/10 px-4 py-3 text-xs font-bold uppercase tracking-widest text-[#e0c1a1] transition hover:bg-[#e0c1a1]/20 focus:outline-none focus:ring-2 focus:ring-[#e0c1a1]/50 active:scale-95"
          onClick={onNew}
          type="button"
        >
          <span aria-hidden="true">+</span>
          New session
        </button>
      </div>

      <nav className="min-h-0 flex-1 space-y-1 overflow-y-auto px-3">
        <p className="mb-2 px-3 text-[10px] font-bold uppercase tracking-widest text-[#9a8f84]">
          Recent chats
        </p>

        {loading ? (
          <p className="px-3 text-xs text-[#9a8f84]">Loading...</p>
        ) : conversations.length === 0 ? (
          <p className="px-3 text-xs leading-5 text-[#9a8f84]">New sessions will appear here.</p>
        ) : (
          <>
            {conversations.map((conversation) => (
              <button
                key={conversation.id}
                onClick={() => onSelect(conversation.id)}
                aria-label={`Open conversation: ${conversation.title || "Untitled prompt"}`}
                className={`w-full px-3 py-2 text-left transition ${
                  selectedConversationId === conversation.id
                    ? "rounded-l-lg border-r-2 border-[#e0c1a1] bg-[#e0c1a1]/10 text-[#e0c1a1]"
                    : "rounded-lg text-[#d1c4b9] hover:bg-[#2d2927] hover:text-[#e8e1dd]"
                }`}
              >
                <span className="block truncate text-xs font-medium">
                  {conversation.title || "Untitled prompt"}
                </span>
              </button>
            ))}
          </>
        )}
      </nav>

      <div className="mt-auto space-y-4 border-t border-[#4e453d]/30 px-4 pt-4">
        <button
          className="flex w-full items-center gap-3 px-3 py-2 text-left text-xs text-[#d1c4b9] transition hover:text-[#e8e1dd]"
          type="button"
        >
          <span className="text-sm" aria-hidden="true">
            []
          </span>
          Documentation
        </button>

        <div className="workspace-glass flex items-center justify-between rounded-xl bg-[#2d2927]/70 p-3">
          <div className="min-w-0">
            <p className="truncate text-xs font-bold text-[#e8e1dd]">{user.name || "Workspace user"}</p>
            <p className={`truncate text-[10px] ${authError ? "text-amber-300" : "text-[#9a8f84]"}`}>
              {authError ? "Auth issue" : user.email}
            </p>
          </div>
          <button
            aria-label="Log out"
            className="rounded-md p-1 text-[#9a8f84] transition hover:text-[#ffb4ab] focus:outline-none focus:ring-2 focus:ring-[#ffb4ab]/50"
            onClick={onLogout}
            type="button"
          >
            <span aria-hidden="true">-&gt;</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
