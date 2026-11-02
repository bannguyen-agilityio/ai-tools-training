import { NavLink } from "react-router-dom";

const LINKS = [
  { to: "/hr/leave", label: "All leave" },
  { to: "/hr/employees", label: "Employees" },
  { to: "/hr/teams", label: "Teams" },
  { to: "/hr/balances", label: "Balances" },
  { to: "/hr/holidays", label: "Holidays" },
  { to: "/hr/report", label: "Monthly report" },
  { to: "/hr/settings", label: "Settings" },
];

/** Section navigation inside the HR tab. Wraps instead of scrolling at 360 px. */
export function HrNav() {
  return (
    <nav aria-label="HR sections" className="subnav no-print">
      <ul>
        {LINKS.map((l) => (
          <li key={l.to}>
            <NavLink to={l.to} className={({ isActive }) => `subnav__link${isActive ? " subnav__link--active" : ""}`}>
              {l.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
