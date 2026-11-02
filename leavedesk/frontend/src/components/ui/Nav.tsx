import { NavLink } from "react-router-dom";

export interface NavItem {
  to: string;
  label: string;
}

export function Nav({ items }: { items: NavItem[] }) {
  return (
    <nav aria-label="Main" className="nav">
      <ul>
        {items.map((item) => (
          <li key={item.to}>
            <NavLink to={item.to} end className="nav__link">
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
