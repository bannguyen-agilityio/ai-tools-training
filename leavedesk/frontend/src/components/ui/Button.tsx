import { forwardRef, type ButtonHTMLAttributes } from "react";
import { Link, type LinkProps } from "react-router-dom";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type Size = "md" | "sm";

function classes(variant: ButtonVariant, size: Size, extra?: string) {
  return `btn btn--${variant} btn--${size} ${extra ?? ""}`.trim();
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: Size;
  loading?: boolean;
}

/** One primary per view. Every size keeps the 44 px minimum target (R31). */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "primary", size = "md", loading = false, className, type = "button", disabled, children, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      className={classes(variant, size, className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading && <span className="spinner" aria-hidden="true" />}
      {children}
      {loading && <span className="visually-hidden"> Loading</span>}
    </button>
  );
});

interface ButtonLinkProps extends LinkProps {
  variant?: ButtonVariant;
  size?: Size;
}

/** A router link that looks like a Button, for navigation actions. */
export function ButtonLink({ variant = "secondary", size = "md", className, ...rest }: ButtonLinkProps) {
  return <Link className={classes(variant, size, className)} {...rest} />;
}
