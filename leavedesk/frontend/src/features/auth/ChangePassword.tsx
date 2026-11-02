import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { api, setCsrfToken } from "../../api/client";
import { Button } from "../../components/ui/Button";
import { ErrorSummary } from "../../components/ui/ErrorSummary";
import { TextField } from "../../components/ui/TextField";
import { useFormFocusFirstError } from "../../components/ui/useFormFocusFirstError";
import { newPassword, PASSWORD_MIN } from "./passwordSchema";

const schema = z
  .object({ current_password: z.string().min(1, "Enter your current password."), new_password: newPassword, confirm: z.string() })
  .refine((v) => v.new_password === v.confirm, { path: ["confirm"], message: "The two passwords do not match." });
type Values = z.infer<typeof schema>;

/** R2: a password change signs out every session, including this one, so the user signs in again. */
export function ChangePassword() {
  const [formError, setFormError] = useState<string | null>(null);
  const { register, handleSubmit, formState } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { current_password: "", new_password: "", confirm: "" },
  });
  const { errors, submitCount, isSubmitting } = formState;
  const formRef = useFormFocusFirstError(submitCount, Object.keys(errors).length + (formError ? 1 : 0));
  const summary = [
    ...(["current_password", "new_password", "confirm"] as const).flatMap((k) =>
      errors[k]?.message ? [{ fieldName: k, message: errors[k].message }] : [],
    ),
    ...(formError ? [{ fieldName: "current_password", message: formError }] : []),
  ];

  async function onSubmit(values: Values) {
    setFormError(null);
    try {
      await api("/auth/password/change", {
        method: "POST",
        body: { current_password: values.current_password, new_password: values.new_password },
      });
      setCsrfToken(null);
      window.location.assign("/sign-in");
    } catch (e) {
      const status = (e as { status?: number }).status;
      setFormError(
        status === 403
          ? (e as Error).message === "Current password is incorrect"
            ? "Your current password is incorrect."
            : "Your session could not be verified. Reload the page and try again."
          : status === 429
            ? "Too many attempts. Wait 15 minutes, then try again."
            : status === 422
              ? (e as Error).message
              : "We could not change your password. Try again in a moment.",
      );
    }
  }

  return (
    <form ref={formRef} noValidate onSubmit={handleSubmit(onSubmit)} aria-label="Change password">
      <h1>Change password</h1>
      <p>You will be signed out everywhere and asked to sign in with the new password.</p>
      <ErrorSummary items={summary} />
      <TextField
        label="Current password"
        type="password"
        autoComplete="current-password"
        error={errors.current_password?.message}
        {...register("current_password")}
      />
      <TextField
        label="New password"
        type="password"
        autoComplete="new-password"
        hint={`At least ${PASSWORD_MIN} characters. Avoid common passwords.`}
        error={errors.new_password?.message}
        {...register("new_password")}
      />
      <TextField
        label="Confirm new password"
        type="password"
        autoComplete="new-password"
        error={errors.confirm?.message}
        {...register("confirm")}
      />
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Saving…" : "Change password"}
      </Button>
    </form>
  );
}
