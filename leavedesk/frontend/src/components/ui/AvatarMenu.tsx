import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { SignOutButton } from "./SignOutButton";
import { useDismiss } from "./useDismiss";

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
        aria-controls={open ? "account-panel" : undefined}
        onClick={() => setOpen((o) => !o)}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <circle cx="12" cy="8" r="4" />
          <path d="M4 21c0-4 3.6-7 8-7s8 3 8 7" />
        </svg>
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
