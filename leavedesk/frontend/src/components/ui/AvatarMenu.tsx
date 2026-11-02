import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { SignOutButton } from "./SignOutButton";
import { useDismiss } from "./useDismiss";

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0].toUpperCase())
    .join("");
}

export function AvatarMenu({ name }: { name: string }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useDismiss(open, ref, () => setOpen(false));
  return (
    <div className="menu" ref={ref}>
      <button
        type="button"
        data-menu-button
        className="icon-btn avatar"
        aria-label={`Account menu, ${name}`}
        aria-expanded={open}
        aria-controls="account-panel"
        onClick={() => setOpen((o) => !o)}
      >
        <span aria-hidden="true">{initials(name)}</span>
      </button>
      {open && (
        <div id="account-panel" className="menu__panel">
          <p className="menu__who">{name}</p>
          <Link className="btn btn--ghost btn--md menu__item" to="/account/password" onClick={() => setOpen(false)}>
            Change password
          </Link>
          <SignOutButton />
        </div>
      )}
    </div>
  );
}
