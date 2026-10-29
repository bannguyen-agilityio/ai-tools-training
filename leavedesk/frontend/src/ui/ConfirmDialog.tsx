import { useEffect, useId, useRef, type KeyboardEvent } from "react";
import { Button } from "./Button";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  /** The exact consequence, e.g. "Cancels your request for Mon 2 Nov - Wed 4 Nov 2026 (3 days)." */
  consequence: string;
  confirmLabel: string;
  keepLabel?: string;
  onConfirm: () => void;
  onKeep: () => void;
}

/** Destructive confirmation. Focus starts on "Keep"; Escape keeps (R31e). */
export function ConfirmDialog({
  open,
  title,
  consequence,
  confirmLabel,
  keepLabel = "Keep",
  onConfirm,
  onKeep,
}: ConfirmDialogProps) {
  const keepRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const titleId = useId();
  const bodyId = useId();

  useEffect(() => {
    if (!open) return;
    const opener = document.activeElement as HTMLElement | null;
    keepRef.current?.focus();
    return () => opener?.focus();
  }, [open]);

  if (!open) return null;

  function onKeyDown(e: KeyboardEvent) {
    if (e.key === "Escape") {
      e.stopPropagation();
      onKeep();
    } else if (e.key === "Tab") {
      const items = dialogRef.current?.querySelectorAll<HTMLElement>("button");
      if (!items || items.length === 0) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  }

  return (
    <div className="dialog-backdrop">
      {/* eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions -- focus trap + Escape for the modal */}
      <div
        ref={dialogRef}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={bodyId}
        className="dialog"
        onKeyDown={onKeyDown}
      >
        <h2 id={titleId}>{title}</h2>
        <p id={bodyId}>{consequence}</p>
        <div className="dialog__actions">
          <Button variant="secondary" onClick={onKeep} ref={keepRef}>
            {keepLabel}
          </Button>
          <Button variant="danger" onClick={onConfirm}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
