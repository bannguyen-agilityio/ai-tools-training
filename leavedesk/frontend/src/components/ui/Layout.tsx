import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { useMe, type Me } from "../../auth/useMe";
import { AvatarMenu } from "./AvatarMenu";
import { NotificationBell } from "./NotificationBell";
import { ThemeToggle } from "./ThemeToggle";

export interface Tab {
  to: string;
  label: string;
  icon: string;
  /** Match nested routes (e.g. /hr/*). */
  prefix?: boolean;
}

/** Presentation only: the server still enforces access on every call. */
export function tabsFor(me: Me | undefined): Tab[] {
  if (!me) return [];
  const tabs: Tab[] = [
    { to: "/", label: "Dashboard", icon: "⌂" },
    { to: "/requests", label: "My requests", icon: "☰", prefix: true },
    { to: "/calendar", label: "Calendar", icon: "▦" },
  ];
  if (me.role === "manager" || me.role === "hr" || me.is_hr_deputy) {
    tabs.push({ to: "/approvals", label: "Approvals", icon: "✓" });
  }
  if (me.role === "hr") tabs.push({ to: "/hr/leave", label: "HR", icon: "⚙", prefix: true });
  return tabs;
}

function CalendarIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M3 10h18M8 3v4M16 3v4" />
    </svg>
  );
}

function TabLinks({ tabs, className }: { tabs: Tab[]; className: string }) {
  return (
    <ul className={className}>
      {tabs.map((t) => (
        <li key={t.to}>
          <NavLink
            to={t.to}
            end={!t.prefix}
            className={({ isActive }) => `tab${isActive ? " tab--active" : ""}`}
          >
            <span className="tab__icon" aria-hidden="true">
              {t.icon}
            </span>
            {t.label}
          </NavLink>
        </li>
      ))}
    </ul>
  );
}

export function Layout({ children }: { children: ReactNode }) {
  const me = useMe().data;
  const tabs = tabsFor(me);
  return (
    <>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <header className="topbar">
        <div className="topbar__inner">
          <span className="topbar__brand">
            <CalendarIcon />
            LeaveDesk
          </span>
          {me && (
            <nav aria-label="Main" className="topbar__tabs">
              <TabLinks tabs={tabs} className="tabs" />
            </nav>
          )}
          <div className="topbar__actions">
            <ThemeToggle />
            {me && <NotificationBell />}
            {me && <AvatarMenu name={me.name} />}
          </div>
        </div>
      </header>
      {me && (
        <nav aria-label="Main, bottom" className="bottombar">
          <TabLinks tabs={tabs} className="tabs tabs--bottom" />
        </nav>
      )}
      <main id="main" tabIndex={-1} className="main">
        {children}
      </main>
    </>
  );
}
