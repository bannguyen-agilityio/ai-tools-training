import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { signInUrl } from "../api/client";
import { ApiError } from "../api/problem";
import { useMe } from "./useMe";

/**
 * Client-side convenience gate for HR screens. The API enforces HR on every call (403);
 * this only avoids showing a screen that cannot work.
 */
export function RequireHr({ children }: { children: ReactNode }) {
  const me = useMe();
  const location = useLocation();
  if (me.isPending) return <p role="status">Loading...</p>;
  if (me.error instanceof ApiError && me.error.status === 401) {
    return <Navigate to={signInUrl(location.pathname + location.search)} replace />;
  }
  if (me.isError) return <p role="alert">Could not check your access. Reload to try again.</p>;
  if (me.data.role !== "hr") {
    return (
      <section>
        <h1>Not allowed</h1>
        <p>Only HR can manage this page.</p>
      </section>
    );
  }
  return <>{children}</>;
}
