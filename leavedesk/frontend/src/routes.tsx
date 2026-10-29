import { Route, Routes } from "react-router-dom";
import { HolidaysPage } from "./features/hr/holidays/HolidaysPage";
import { SampleForm } from "./SampleForm";
import { Layout } from "./ui/Layout";
import type { NavItem } from "./ui/Nav";

const NAV: NavItem[] = [
  { to: "/", label: "Home" },
  { to: "/sample-form", label: "Sample form" },
  { to: "/hr/holidays", label: "Holidays" },
];

export function AppRoutes() {
  return (
    <Layout nav={NAV}>
      <Routes>
        <Route path="/" element={<h1>LeaveDesk</h1>} />
        <Route path="/sample-form" element={<SampleForm />} />
        <Route path="/hr/holidays" element={<HolidaysPage />} />
        <Route path="/sign-in" element={<h1>Sign in</h1>} />
        <Route path="*" element={<h1>Page not found</h1>} />
      </Routes>
    </Layout>
  );
}
