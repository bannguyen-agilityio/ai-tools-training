import type { ReactNode } from "react";

/** Colour is never the only signal: the icon and the "Error:" text carry it too (R31b). */
export function FormError({ id, children }: { id?: string; children: ReactNode }) {
  return (
    <p id={id} className="form-error">
      <span aria-hidden="true">⚠ </span>
      <span className="visually-hidden">Error: </span>
      {children}
    </p>
  );
}
