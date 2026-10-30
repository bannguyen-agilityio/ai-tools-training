import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, useSearchParams } from "react-router-dom";
import { z } from "zod";
import { api, safeNext, setCsrfToken } from "../../api/client";
import { Button } from "../../ui/Button";
import { ErrorSummary } from "../../ui/ErrorSummary";
import { TextField } from "../../ui/TextField";
import { useFormFocusFirstError } from "../../ui/useFormFocusFirstError";

const schema = z.object({
  email: z.string().trim().min(1, "Enter your work email, for example linh.tran@asnet.com.vn."),
  password: z.string().min(1, "Enter your password."),
});
type Values = z.infer<typeof schema>;

interface Me {
  csrf_token: string;
}

/** R1: email + password. The 401 flow sends people here with `?next=` so they land back where they were (R2). */
export function SignIn() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const queryClient = useQueryClient();
  const [formError, setFormError] = useState<string | null>(null);
  const { register, handleSubmit, formState } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "" },
  });
  const { errors, submitCount, isSubmitting } = formState;
  const formRef = useFormFocusFirstError(submitCount, Object.keys(errors).length + (formError ? 1 : 0));
  const summary = [
    ...(["email", "password"] as const).flatMap((k) =>
      errors[k]?.message ? [{ fieldName: k, message: errors[k].message }] : [],
    ),
    ...(formError ? [{ fieldName: "email", message: formError }] : []),
  ];

  async function onSubmit(values: Values) {
    setFormError(null);
    try {
      const me = await api<Me>("/auth/login", { method: "POST", body: values, noRedirect: true });
      setCsrfToken(me.csrf_token);
      await queryClient.invalidateQueries({ queryKey: ["me"] });
      navigate(safeNext(params.get("next")), { replace: true });
    } catch (e) {
      const status = (e as { status?: number }).status;
      setFormError(
        status === 429
          ? "Too many attempts. Wait 15 minutes, then try again."
          : status === 401
            ? "Email or password is incorrect."
            : "We could not sign you in. Try again in a moment.",
      );
    }
  }

  return (
    <form ref={formRef} noValidate onSubmit={handleSubmit(onSubmit)} aria-label="Sign in">
      <h1>Sign in</h1>
      <ErrorSummary items={summary} />
      <TextField
        label="Work email"
        type="email"
        autoComplete="username"
        error={errors.email?.message}
        {...register("email")}
      />
      <TextField
        label="Password"
        type="password"
        autoComplete="current-password"
        error={errors.password?.message}
        {...register("password")}
      />
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Signing in…" : "Sign in"}
      </Button>
    </form>
  );
}
