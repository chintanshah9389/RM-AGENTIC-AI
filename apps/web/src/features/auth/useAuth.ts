import { useMemo } from "react";

export type AuthUser = {
  id: string;
  email: string;
  full_name: string;
  role: string;
};

export function useAuth() {
  const token = localStorage.getItem("abcrm_token");
  const raw = localStorage.getItem("abcrm_user");
  const user = useMemo(() => {
    if (!raw) return null;
    try {
      return JSON.parse(raw) as AuthUser;
    } catch {
      return null;
    }
  }, [raw]);

  return { token, user };
}

export function persistAuth(token: string, user: AuthUser) {
  localStorage.setItem("abcrm_token", token);
  localStorage.setItem("abcrm_user", JSON.stringify(user));
}

export function clearAuth() {
  localStorage.removeItem("abcrm_token");
  localStorage.removeItem("abcrm_user");
}
