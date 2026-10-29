export interface SummaryItem {
  /** DOM id of the invalid control, so the link can focus it. */
  fieldId?: string;
  message: string;
}

/** Announced (role="alert") list of what to fix; each item links to its field (R31d). */
export function ErrorSummary({ items }: { items: SummaryItem[] }) {
  if (items.length === 0) return null;
  return (
    <div role="alert" className="error-summary">
      <p className="error-summary__title">
        <span aria-hidden="true">⚠ </span>
        {items.length === 1 ? "1 thing needs fixing" : `${items.length} things need fixing`}
      </p>
      <ul>
        {items.map((item) => (
          <li key={`${item.fieldId}-${item.message}`}>
            {item.fieldId ? <a href={`#${item.fieldId}`}>{item.message}</a> : item.message}
          </li>
        ))}
      </ul>
    </div>
  );
}
