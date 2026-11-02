import type { ReactNode } from "react";
import { Nav, type NavItem } from "./Nav";
import { SignOutButton } from "./SignOutButton";

export function Layout({
  nav,
  signedIn = false,
  children,
}: {
  nav: NavItem[];
  signedIn?: boolean;
  children: ReactNode;
}) {
  return (
    <>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <header className="header">
        <div className="header__top">
          <span className="header__brand">LeaveDesk</span>
          {signedIn && <SignOutButton />}
        </div>
        <Nav items={nav} />
      </header>
      <main id="main" tabIndex={-1} className="main">
        {children}
      </main>
    </>
  );
}
