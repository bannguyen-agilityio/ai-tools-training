export type Status = "pending" | "approved" | "rejected" | "cancelled";

const META: Record<Status, { label: string; icon: string }> = {
  pending: { label: "Pending", icon: "◷" },
  approved: { label: "Approved", icon: "✓" },
  rejected: { label: "Rejected", icon: "✕" },
  cancelled: { label: "Cancelled", icon: "⊘" },
};

/** Always icon plus text label, so status is never colour alone (R31, R27). */
export function StatusBadge({ status }: { status: Status }) {
  const m = META[status];
  return (
    <span className={`badge badge--${status}`}>
      <span aria-hidden="true">{m.icon}</span>
      {m.label}
    </span>
  );
}
