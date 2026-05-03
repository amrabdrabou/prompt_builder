import { API_BASE_URL, apiFetch } from "./client";
import type { User } from "../types";

export function getCurrentUser(): Promise<User> {
  return apiFetch<User>("/auth/me");
}

export function logout(): Promise<{ message: string }> {
  return apiFetch<{ message: string }>("/auth/logout", {
    method: "POST",
  });
}

export function redirectToGoogleLogin() {
  window.location.assign(`${API_BASE_URL}/auth/google/login`);
}
