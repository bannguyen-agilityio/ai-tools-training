import type { ReactNode } from "react";

export interface Column<T> {
  key: string;
  header: string;
  cell: (row: T) => ReactNode;
  /** Right-aligned, tabular figures. */
  numeric?: boolean;
  /** Row heading cell (first column). */
  primary?: boolean;
}

/**
 * A table from 768 px up; below it each row becomes a stacked item (CSS only), so a
 * 360 px screen never scrolls sideways. Same DOM, so it works for keyboard and AT.
 */
export function DataList<T>({
  caption,
  columns,
  rows,
  rowKey,
  compact = false,
}: {
  caption: string;
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  /** Below 768 px: dates, then "Type · Days", status at the right (dashboard list). */
  compact?: boolean;
}) {
  return (
    <table className={compact ? "data-list data-list--compact" : "data-list"}>
      <caption className="visually-hidden">{caption}</caption>
      <thead>
        <tr>
          {columns.map((c) => (
            <th key={c.key} scope="col" className={c.numeric ? "num" : undefined}>
              {c.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={rowKey(r)}>
            {columns.map((c) =>
              c.primary ? (
                <th key={c.key} scope="row" data-label={c.header}>
                  {c.cell(r)}
                </th>
              ) : (
                <td key={c.key} data-label={c.header} className={c.numeric ? "num" : undefined}>
                  {c.cell(r)}
                </td>
              ),
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
