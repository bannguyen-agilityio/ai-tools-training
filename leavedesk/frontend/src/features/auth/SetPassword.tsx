import { TokenPasswordForm } from "./TokenPasswordForm";

/** R3: invite link (48 h, single use) lands here; HR never sees the password or the link. */
export function SetPassword() {
  return (
    <TokenPasswordForm
      title="Set your password"
      endpoint="/auth/invite/accept"
      submitLabel="Set password"
      expiredHint="Invite links last 48 hours and work once. Ask HR to send you a new invite."
    />
  );
}
