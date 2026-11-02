import type { ReactNode } from "react";

/** One centred card for the pre-login pages and change password. */
export function AuthCard({ children }: { children: ReactNode }) {
  return <div className="auth card">{children}</div>;
}
