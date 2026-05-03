import { useCallback, useEffect, useRef } from "react";
import { AppShell } from "./components/layout/AppShell";
import { Sidebar } from "./components/layout/Sidebar";
import { ChatWorkspace } from "./components/chat/ChatWorkspace";
import { useChatStream } from "./hooks/useChatStream";
import { useAuth } from "./hooks/useAuth";
import { useConversations } from "./hooks/useConversations";
import { useRoute, type AppRoute, type AuthRoute } from "./hooks/useRoute";
import { AuthPage } from "./pages/auth/AuthPage";
import { createConversation } from "./api/conversations";
import type { ChatMessage, User } from "./types";

function toChatMessages(messages: Array<{ id: string; role: "user" | "assistant"; content: string }>): ChatMessage[] {
  return messages.map((message) => ({
    id: message.id,
    role: message.role,
    content: message.content,
  }));
}

interface WorkspaceProps {
  user: User;
  route: AppRoute;
  authError?: string | null;
  onNavigate: (route: AppRoute, replace?: boolean) => void;
  onLogout: () => void;
}

function Workspace({ user, route, authError, onNavigate, onLogout }: WorkspaceProps) {
  const conversations = useConversations();
  const chat = useChatStream(() => {
    void conversations.refresh();
  });
  const {
    conversations: conversationItems,
    loading: conversationsLoading,
    error: conversationsError,
    loadConversation,
  } = conversations;
  const {
    activity,
    conversationId,
    conversationState,
    error: chatError,
    hydrate,
    messages,
    reportError,
    reset,
    sendMessage,
    status,
  } = chat;
  const lastLoadedConversationRef = useRef<string | null>(null);

  const handleSelectConversation = useCallback(async (id: string) => {
    try {
      lastLoadedConversationRef.current = id;
      onNavigate({ name: "conversation", path: `/c/${id}`, conversationId: id });
      const bundle = await loadConversation(id);
      hydrate(
        id,
        toChatMessages(bundle.messages),
        bundle.detail.conversation_state,
        bundle.finalPrompt,
      );
    } catch {
      lastLoadedConversationRef.current = null;
      reportError("Could not load conversation. Please try again.");
    }
  }, [hydrate, loadConversation, onNavigate, reportError]);

  const handleNewPrompt = useCallback(() => {
    reset();
    lastLoadedConversationRef.current = null;
    onNavigate({ name: "home", path: "/" });
  }, [onNavigate, reset]);

  const handleSend = useCallback(async (message: string) => {
    if (conversationId || route.name === "conversation") {
      await sendMessage(message);
      return;
    }

    try {
      const conversation = await createConversation();
      lastLoadedConversationRef.current = conversation.id;
      hydrate(conversation.id, [], conversation.conversation_state, null);
      onNavigate(
        {
          name: "conversation",
          path: `/c/${conversation.id}`,
          conversationId: conversation.id,
        },
        true,
      );
      void conversations.refresh();
      await sendMessage(message, conversation.id);
    } catch {
      reportError("Could not start a conversation. Please try again.");
    }
  }, [
    conversationId,
    conversations,
    hydrate,
    onNavigate,
    reportError,
    route.name,
    sendMessage,
  ]);

  useEffect(() => {
    if (route.name !== "conversation") {
      lastLoadedConversationRef.current = null;
      return;
    }

    if (lastLoadedConversationRef.current === route.conversationId) {
      return;
    }

    let cancelled = false;
    const routeConversationId = route.conversationId;

    async function loadConversationFromRoute() {
      try {
        const bundle = await loadConversation(routeConversationId);
        if (cancelled) {
          return;
        }

        hydrate(
          routeConversationId,
          toChatMessages(bundle.messages),
          bundle.detail.conversation_state,
          bundle.finalPrompt,
        );
        lastLoadedConversationRef.current = routeConversationId;
      } catch {
        if (!cancelled) {
          reportError("Could not load conversation. Please check the URL and try again.");
        }
      }
    }

    void loadConversationFromRoute();

    return () => {
      cancelled = true;
    };
  }, [hydrate, loadConversation, reportError, route]);

  useEffect(() => {
    if (!conversationId || route.name === "conversation") {
      return;
    }

    lastLoadedConversationRef.current = conversationId;
    onNavigate(
      {
        name: "conversation",
        path: `/c/${conversationId}`,
        conversationId,
      },
      true,
    );
  }, [conversationId, onNavigate, route.name]);

  return (
    <AppShell>
      <Sidebar
        conversations={conversationItems}
        selectedConversationId={conversationId}
        loading={conversationsLoading}
        onSelect={handleSelectConversation}
        onNew={handleNewPrompt}
        user={user}
        authError={authError}
        onLogout={onLogout}
      />
      <ChatWorkspace
        messages={messages}
        status={status}
        activity={activity}
        conversationState={conversationState}
        conversationReady={
          route.name === "conversation" && conversationId === route.conversationId
        }
        error={chatError ?? conversationsError}
        onSend={handleSend}
      />
    </AppShell>
  );
}

export default function App() {
  const auth = useAuth();
  const { route, navigate } = useRoute();

  const navigateAuth = useCallback((nextRoute: AuthRoute) => {
    if (nextRoute === "/register") {
      navigate({ name: "register", path: "/register" });
      return;
    }

    navigate({ name: "login", path: "/login" });
  }, [navigate]);

  if (auth.status === "checking") {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-canvas px-4 text-sm text-ink-subtle">
        Checking your session...
      </div>
    );
  }

  if (!auth.user) {
    if (route.name === "register") {
      return <AuthPage mode="register" onNavigate={navigateAuth} />;
    }

    return <AuthPage mode="login" onNavigate={navigateAuth} />;
  }

  return (
    <Workspace
      user={auth.user}
      route={route}
      authError={auth.error}
      onNavigate={navigate}
      onLogout={async () => {
        await auth.signOut();
        navigate({ name: "login", path: "/login" });
      }}
    />
  );
}
