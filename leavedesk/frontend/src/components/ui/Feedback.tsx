import type { ReactNode } from "react";
import { Button } from "./Button";

type Tone = "info" | "warning" | "danger" | "success";
const ICON: Record<Tone, string> = { info: "ℹ", warning: "⚠", danger: "⚠", success: "✓" };
const SR: Record<Tone, string> = { info: "Info", warning: "Warning", danger: "Error", success: "Success" };

/** Inline message; role=alert for errors, status otherwise, so it is announced (aria-live). */
export function Alert({
  tone = "info",
  children,
  onRetry,
}: {
  tone?: Tone;
  children: ReactNode;
  onRetry?: () => void;
}) {
  return (
    <div className={`alert alert--${tone}`} role={tone === "danger" ? "alert" : "status"}>
      <span aria-hidden="true">{ICON[tone]}</span>
      <p className="alert__text">
        <span className="visually-hidden">{SR[tone]}: </span>
        {children}
      </p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  );
}

export function EmptyState({ title, children, action }: { title: string; children?: ReactNode; action?: ReactNode }) {
  return (
    <div className="empty">
      <p className="empty__title">{title}</p>
      {children && <p className="empty__body">{children}</p>}
      {action}
    </div>
  );
}

/** Placeholder block; size it with the width/height classes so layout does not shift. */
export function Skeleton({ className = "" }: { className?: string }) {
  return <span className={`skeleton ${className}`.trim()} aria-hidden="true" />;
}

/** Wrap skeleton groups so assistive tech hears one "Loading" instead of nothing. */
export function Loading({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div role="status" aria-busy="true">
      <span className="visually-hidden">{label}</span>
      {children}
    </div>
  );
}
