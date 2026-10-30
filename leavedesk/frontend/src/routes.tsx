import { Route, Routes } from "react-router-dom";
import { RequireHr } from "./auth/RequireHr";
import { useMe } from "./auth/useMe";
import { ApprovalList } from "./features/approvals/ApprovalList";
import { Dashboard } from "./features/dashboard/Dashboard";
import { MyRequests } from "./features/requests/MyRequests";
import { NewRequest } from "./features/requests/NewRequest";
import { RequestDetail } from "./features/requests/RequestDetail";
import { BalancesPage } from "./features/hr/balances/BalancesPage";
import { EmployeesPage } from "./features/hr/employees/EmployeesPage";
import { HolidaysPage } from "./features/hr/holidays/HolidaysPage";
import { SettingsPage } from "./features/hr/settings/SettingsPage";
import { TeamsPage } from "./features/hr/teams/TeamsPage";
import { SampleForm } from "./SampleForm";
import { Layout } from "./ui/Layout";
import type { NavItem } from "./ui/Nav";

const NAV: NavItem[] = [
  { to: "/", label: "Home" },
  { to: "/requests", label: "My requests" },
  { to: "/sample-form", label: "Sample form" },
];
const HR_NAV: NavItem[] = [
  { to: "/hr/employees", label: "Employees" },
  { to: "/hr/balances", label: "Balances" },
  { to: "/hr/teams", label: "Teams" },
  { to: "/hr/holidays", label: "Holidays" },
  { to: "/hr/settings", label: "Settings" },
];

export function AppRoutes() {
  const me = useMe();
  const role = me.data?.role;
  const deciders: NavItem[] =
    role === "manager" || role === "hr" || me.data?.is_hr_deputy
      ? [{ to: "/approvals", label: "Approvals" }]
      : [];
  const base = [...NAV, ...deciders];
  const nav = role === "hr" ? [...base, ...HR_NAV] : base;
  return (
    <Layout nav={nav}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/requests" element={<MyRequests />} />
        <Route path="/requests/new" element={<NewRequest />} />
        <Route path="/requests/:id" element={<RequestDetail />} />
        <Route path="/approvals" element={<ApprovalList />} />
        <Route path="/sample-form" element={<SampleForm />} />
        <Route
          path="/hr/holidays"
          element={
            <RequireHr>
              <HolidaysPage />
            </RequireHr>
          }
        />
        <Route
          path="/hr/employees"
          element={
            <RequireHr>
              <EmployeesPage />
            </RequireHr>
          }
        />
        <Route
          path="/hr/balances"
          element={
            <RequireHr>
              <BalancesPage />
            </RequireHr>
          }
        />
        <Route
          path="/hr/teams"
          element={
            <RequireHr>
              <TeamsPage />
            </RequireHr>
          }
        />
        <Route
          path="/hr/settings"
          element={
            <RequireHr>
              <SettingsPage />
            </RequireHr>
          }
        />
        <Route path="/sign-in" element={<h1>Sign in</h1>} />
        <Route path="*" element={<h1>Page not found</h1>} />
      </Routes>
    </Layout>
  );
}
