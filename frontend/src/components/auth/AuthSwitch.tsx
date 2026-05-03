import type { AuthRoute } from "../../hooks/useRoute";

interface AuthSwitchProps {
  label: string;
  action: string;
  route: AuthRoute;
  onNavigate: (route: AuthRoute) => void;
}

export function AuthSwitch({ label, action, route, onNavigate }: AuthSwitchProps) {
  return (
    <p className="mt-8 text-center text-sm leading-5 text-[#9a8f84]">
      {label}{" "}
      <button
        className="ml-1 font-semibold text-[#e0c1a1] underline-offset-4 hover:underline focus:outline-none focus:ring-2 focus:ring-[#e0c1a1]/70"
        onClick={() => onNavigate(route)}
        type="button"
      >
        {action}
      </button>
    </p>
  );
}
