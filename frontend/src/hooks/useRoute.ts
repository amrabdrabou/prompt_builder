import { useCallback, useEffect, useState } from "react";

export type AuthRoute = "/login" | "/register";
export type AppRoute =
  | { name: "home"; path: "/" }
  | { name: "login"; path: "/login" }
  | { name: "register"; path: "/register" }
  | { name: "conversation"; path: `/c/${string}`; conversationId: string };

function normalizePath(pathname: string): AppRoute {
  if (pathname === "/register") {
    return { name: "register", path: "/register" };
  }

  if (pathname === "/login") {
    return { name: "login", path: "/login" };
  }

  const conversationMatch = pathname.match(/^\/c\/([^/]+)$/);
  if (conversationMatch) {
    const conversationId = decodeURIComponent(conversationMatch[1]);
    return {
      name: "conversation",
      path: `/c/${conversationId}`,
      conversationId,
    };
  }

  return { name: "home", path: "/" };
}

export function useRoute() {
  const [route, setRoute] = useState<AppRoute>(() => normalizePath(window.location.pathname));

  const navigate = useCallback((nextRoute: AppRoute, replace = false) => {
    if (replace) {
      window.history.replaceState({}, "", nextRoute.path);
    } else {
      window.history.pushState({}, "", nextRoute.path);
    }
    setRoute(nextRoute);
  }, []);

  useEffect(() => {
    function handlePopState() {
      setRoute(normalizePath(window.location.pathname));
    }

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  return {
    route,
    navigate,
  };
}
