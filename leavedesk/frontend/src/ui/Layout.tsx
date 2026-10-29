import type { ReactNode } from "react";
import { Nav, type NavItem } from "./Nav";

export function Layout({ nav, children }: { nav: NavItem[]; children: ReactNode }) {
  return (
    <>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <header className="header">
        <span className="header__brand">LeaveDesk</span>
        <Nav items={nav} />
      </header>
      <main id="main" tabIndex={-1} className="main">
        {children}
      </main>
    </>
  );
}
