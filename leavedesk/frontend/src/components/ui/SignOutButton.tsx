import { useState } from "react";
import { api, setCsrfToken, signInPath } from "../../api/client";
import { Button } from "./Button";

/** Ends the session on the server, then drops the local CSRF token and returns to sign-in (R2). */
export function SignOutButton() {
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  async function signOut() {
    setBusy(true);
    setFailed(false);
    try {
      await api("/auth/logout", { method: "POST", noRedirect: true });
    } catch (e) {
      // 401: already signed out, so leave. Anything else (CSRF 403, 5xx, offline) means the
      // session may still be live: stay on the page and say so instead of pretending.
      if ((e as { status?: number }).status !== 401) {
        setBusy(false);
        setFailed(true);
        return;
      }
    }
    setCsrfToken(null);
    window.location.assign(signInPath);
  }
  return (
    <>
      <Button variant="secondary" onClick={signOut} disabled={busy}>
        Sign out
      </Button>
      {failed && (
        <span role="alert" className="header__error">
          Could not sign out. Try again.
        </span>
      )}
    </>
  );
}
