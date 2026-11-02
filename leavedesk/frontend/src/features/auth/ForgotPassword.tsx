import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { z } from "zod";
import { api } from "../../api/client";
import { Button } from "../../components/ui/Button";
import { ErrorSummary } from "../../components/ui/ErrorSummary";
import { TextField } from "../../components/ui/TextField";
import { useFormFocusFirstError } from "../../components/ui/useFormFocusFirstError";

const schema = z.object({
  email: z.string().trim().min(1, "Enter your work email, for example linh.tran@asnet.com.vn."),
});
type Values = z.infer<typeof schema>;

/** R3: the answer is the same for every address, so the page never says whether an account exists. */
export function ForgotPassword() {
  const [sent, setSent] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const { register, handleSubmit, formState } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { email: "" },
  });
  const { errors, submitCount, isSubmitting } = formState;
  const formRef = useFormFocusFirstError(submitCount, Object.keys(errors).length + (formError ? 1 : 0));

  async function onSubmit(values: Values) {
    setFormError(null);
    try {
      await api("/auth/reset/request", { method: "POST", body: values, noRedirect: true });
      setSent(true);
    } catch {
      setFormError("We could not send the request. Try again in a moment.");
    }
  }

  if (sent) {
    return (
      <section aria-labelledby="sent-title">
        <h1 id="sent-title">Check your email</h1>
        <p role="status">
          If that address belongs to a LeaveDesk account, we have sent a link to reset the password. It works once, for
          1 hour.
        </p>
        <p>
          <Link to="/sign-in">Back to sign in</Link>
        </p>
      </section>
    );
  }

  const summary = [
    ...(errors.email?.message ? [{ fieldName: "email", message: errors.email.message }] : []),
    ...(formError ? [{ fieldName: "email", message: formError }] : []),
  ];

  return (
    <form ref={formRef} noValidate onSubmit={handleSubmit(onSubmit)} aria-label="Forgot password">
      <h1>Forgot your password?</h1>
      <p>Enter your work email and we will send you a link to choose a new one.</p>
      <ErrorSummary items={summary} />
      <TextField
        label="Work email"
        type="email"
        autoComplete="username"
        error={errors.email?.message}
        {...register("email")}
      />
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Sending…" : "Send reset link"}
      </Button>
      <p>
        <Link to="/sign-in">Back to sign in</Link>
      </p>
    </form>
  );
}
