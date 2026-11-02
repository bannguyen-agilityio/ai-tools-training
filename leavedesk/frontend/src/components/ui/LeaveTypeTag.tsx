const NAME = { annual: "Annual", unpaid: "Unpaid", sick: "Sick" } as const;

/**
 * Takes the type exactly as the API returned it. A missing type (Sick redacted by the
 * server, spec section 8) renders the neutral "Off" style. Nothing is inferred, and the
 * markup carries no class, title or data attribute that depends on the hidden type.
 */
export function LeaveTypeTag({ type, label }: { type: "annual" | "sick" | "unpaid" | null | undefined; label?: string | null }) {
  if (!type) return <span className="tag tag--off">{label ?? "Off"}</span>;
  return <span className={`tag tag--${type === "sick" ? "off" : type}`}>{NAME[type]}</span>;
}
