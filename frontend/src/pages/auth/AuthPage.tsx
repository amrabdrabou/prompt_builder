import { AuthCard } from "../../components/auth/AuthCard";
import { AuthShell } from "../../components/auth/AuthShell";
import { AuthSwitch } from "../../components/auth/AuthSwitch";
import { GoogleAuthButton } from "../../components/auth/GoogleAuthButton";
import type { AuthRoute } from "../../hooks/useRoute";

type AuthMode = "login" | "register";

const content: Record<
  AuthMode,
  {
    title: string;
    description: string;
    button: string;
    switchLabel: string;
    switchAction: string;
    switchRoute: AuthRoute;
  }
> = {
  login: {
    title: "Welcome back",
    description:
      "Continue with your Google account to access your workspace.",
    button: "Continue with Google",
    switchLabel: "Don't have an account?",
    switchAction: "Create an account",
    switchRoute: "/register",
  },
  register: {
    title: "Create account",
    description:
      "Use your Google account to start a precision-focused prompt workspace.",
    button: "Create with Google",
    switchLabel: "Already have an account?",
    switchAction: "Sign in",
    switchRoute: "/login",
  },
};

interface AuthPageProps {
  mode: AuthMode;
  onNavigate: (route: AuthRoute) => void;
}

export function AuthPage({ mode, onNavigate }: AuthPageProps) {
  const copy = content[mode];

  return (
    <AuthShell>
      <AuthCard title={copy.title} description={copy.description}>
        <GoogleAuthButton>{copy.button}</GoogleAuthButton>
        <AuthSwitch
          label={copy.switchLabel}
          action={copy.switchAction}
          route={copy.switchRoute}
          onNavigate={onNavigate}
        />
      </AuthCard>
    </AuthShell>
  );
}
