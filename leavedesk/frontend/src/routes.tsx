import { Route, Routes } from "react-router-dom";
import { RequireHr } from "./auth/RequireHr";
import { useMe } from "./auth/useMe";
import { EmployeesPage } from "./features/hr/employees/EmployeesPage";
import { HolidaysPage } from "./features/hr/holidays/HolidaysPage";
import { TeamsPage } from "./features/hr/teams/TeamsPage";
import { SampleForm } from "./SampleForm";
import { Layout } from "./ui/Layout";
import type { NavItem } from "./ui/Nav";

const NAV: NavItem[] = [
  { to: "/", label: "Home" },
  { to: "/sample-form", label: "Sample form" },
];
const HR_NAV: NavItem[] = [
  { to: "/hr/employees", label: "Employees" },
  { to: "/hr/teams", label: "Teams" },
  { to: "/hr/holidays", label: "Holidays" },
];

export function AppRoutes() {
  const me = useMe();
  const nav = me.data?.role === "hr" ? [...NAV, ...HR_NAV] : NAV;
  return (
    <Layout nav={nav}>
      <Routes>
        <Route path="/" element={<h1>LeaveDesk</h1>} />
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
          path="/hr/teams"
          element={
            <RequireHr>
              <TeamsPage />
            </RequireHr>
          }
        />
        <Route path="/sign-in" element={<h1>Sign in</h1>} />
        <Route path="*" element={<h1>Page not found</h1>} />
      </Routes>
    </Layout>
  );
}
