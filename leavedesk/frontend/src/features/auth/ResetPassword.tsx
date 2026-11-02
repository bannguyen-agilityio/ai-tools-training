import { TokenPasswordForm } from "./TokenPasswordForm";

/** R3: reset link (1 h, single use). Confirming signs out every session (R2). */
export function ResetPassword() {
  return (
    <TokenPasswordForm
      title="Reset your password"
      endpoint="/auth/reset/confirm"
      submitLabel="Reset password"
      newLinkTo="/forgot-password"
      newLinkLabel="Request a new link"
    />
  );
}
