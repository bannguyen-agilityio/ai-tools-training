import { Button } from "../../../ui/Button";
import type { Balance, BalanceRow } from "./api";

function find(balances: Balance[], code: "annual" | "sick"): Balance | undefined {
  return balances.find((b) => b.leave_type_code === code);
}

interface Props {
  rows: BalanceRow[];
  onSelect?: (row: BalanceRow) => void;
  /** Adds a blank "Checked" column for staff to tick on the printed launch list (C-9). */
  checkColumn?: boolean;
}

export function BalanceList({ rows, onSelect, checkColumn }: Props) {
  return (
    <table className="balance-table">
      <caption className="visually-hidden">Leave balances</caption>
      <thead>
        <tr>
          <th scope="col">Employee</th>
          <th scope="col">Annual available</th>
          <th scope="col">Of which carried</th>
          <th scope="col">Sick available</th>
          {checkColumn ? <th scope="col">Checked</th> : <th scope="col">Actions</th>}
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.employee_id}>
            <th scope="row">
              {r.employee_name}
              <br />
              <span className="balance-table__email">{r.email}</span>
            </th>
            <td>{find(r.balances, "annual")?.available ?? "0.0"}</td>
            <td>{find(r.balances, "annual")?.carried_remaining ?? "0.0"}</td>
            <td>{find(r.balances, "sick")?.available ?? "0.0"}</td>
            {checkColumn ? (
              <td className="balance-table__check" />
            ) : (
              <td>
                <Button variant="secondary" aria-label={`Enter or correct balances for ${r.employee_name}`} onClick={() => onSelect?.(r)}>
                  Enter or correct
                </Button>
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
