import { useState } from "react";
import { api, setCsrfToken, signInPath } from "../api/client";
import { Button } from "./Button";

/** Ends the session on the server, then drops the local CSRF token and returns to sign-in (R2). */
export function SignOutButton() {
  const [busy, setBusy] = useState(false);
  async function signOut() {
    setBusy(true);
    try {
      await api("/auth/logout", { method: "POST", noRedirect: true });
    } catch {
      // Already signed out (401) or the session expired: either way, leave.
    }
    setCsrfToken(null);
    window.location.assign(signInPath);
  }
  return (
    <Button variant="secondary" onClick={signOut} disabled={busy}>
      Sign out
    </Button>
  );
}
