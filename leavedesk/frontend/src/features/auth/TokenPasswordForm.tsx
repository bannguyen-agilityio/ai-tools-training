import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { z } from "zod";
import { api, setCsrfToken } from "../../api/client";
import { Button } from "../../components/ui/Button";
import { ErrorSummary } from "../../components/ui/ErrorSummary";
import { TextField } from "../../components/ui/TextField";
import { useFormFocusFirstError } from "../../components/ui/useFormFocusFirstError";
import { newPassword, PASSWORD_MIN } from "./passwordSchema";
import { PageHeader } from "../../components/ui/Card";

const schema = z
  .object({ password: newPassword, confirm: z.string() })
  .refine((v) => v.password === v.confirm, { path: ["confirm"], message: "The two passwords do not match." });
type Values = z.infer<typeof schema>;

interface Props {
  title: string;
  endpoint: string;
  submitLabel: string;
  /** Invite links cannot be self-served: HR re-sends them (R3). */
  expiredHint?: string;
  /** Where "request a new link" goes when the link is expired, used or missing. */
  newLinkTo?: string;
  newLinkLabel?: string;
}

/** Shared by Set password (R3 invite) and Reset password (R3 reset): token from `?token=`, never stored. */
export function TokenPasswordForm({ title, endpoint, submitLabel, newLinkTo, newLinkLabel, expiredHint }: Props) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const queryClient = useQueryClient();
  // Keep the token in memory only: take it out of the address bar, history and Referer.
  const [token] = useState(() => params.get("token") ?? "");
  useEffect(() => {
    if (params.has("token")) navigate({ search: "" }, { replace: true });
  }, [params, navigate]);
  const [formError, setFormError] = useState<string | null>(null);
  const [badLink, setBadLink] = useState(token === "");
  const { register, handleSubmit, formState } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { password: "", confirm: "" },
  });
  const { errors, submitCount, isSubmitting } = formState;
  const formRef = useFormFocusFirstError(submitCount, Object.keys(errors).length + (formError ? 1 : 0));

  if (badLink) {
    return (
      <section aria-labelledby="link-title">
        <PageHeader title="This link has expired or was already used" titleId="link-title" />
        <p>{expiredHint ?? "Links work once. Request a new one and use it within the time shown in the email."}</p>
        <p>
          <Link to={newLinkTo ?? "/sign-in"} className="btn btn--primary">
            {newLinkLabel ?? "Back to sign in"}
          </Link>
        </p>
      </section>
    );
  }

  const summary = [
    ...(["password", "confirm"] as const).flatMap((k) =>
      errors[k]?.message ? [{ fieldName: k, message: errors[k].message }] : [],
    ),
    ...(formError ? [{ fieldName: "password", message: formError }] : []),
  ];

  async function onSubmit(values: Values) {
    setFormError(null);
    try {
      await api(endpoint, { method: "POST", body: { token, password: values.password }, noRedirect: true });
      setCsrfToken(null); // the server ended every session; drop what the old one left behind
      queryClient.clear();
      navigate("/sign-in", { replace: true, state: { passwordSet: true } });
    } catch (e) {
      const status = (e as { status?: number }).status;
      if (status === 400) setBadLink(true);
      else if (status === 422) setFormError((e as Error).message);
      else setFormError("We could not save your password. Try again in a moment.");
    }
  }

  return (
    <form ref={formRef} noValidate onSubmit={handleSubmit(onSubmit)} aria-label={title}>
      <h1>{title}</h1>
      <ErrorSummary items={summary} />
      <TextField
        label="New password"
        type="password"
        autoComplete="new-password"
        hint={`At least ${PASSWORD_MIN} characters. Avoid common passwords.`}
        error={errors.password?.message}
        {...register("password")}
      />
      <TextField
        label="Confirm new password"
        type="password"
        autoComplete="new-password"
        error={errors.confirm?.message}
        {...register("confirm")}
      />
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Saving…" : submitLabel}
      </Button>
    </form>
  );
}
