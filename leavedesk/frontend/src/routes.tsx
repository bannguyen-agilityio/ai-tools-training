import { Route, Routes } from "react-router-dom";
import { RequireHr } from "./auth/RequireHr";
import { ChangePassword } from "./features/auth/ChangePassword";
import { ForgotPassword } from "./features/auth/ForgotPassword";
import { ResetPassword } from "./features/auth/ResetPassword";
import { SetPassword } from "./features/auth/SetPassword";
import { SignIn } from "./features/auth/SignIn";
import { ApprovalList } from "./features/approvals/ApprovalList";
import { CalendarPage } from "./features/calendar/CalendarPage";
import { Dashboard } from "./features/dashboard/Dashboard";
import { MyRequests } from "./features/requests/MyRequests";
import { NewRequest } from "./features/requests/NewRequest";
import { RequestDetail } from "./features/requests/RequestDetail";
import { BalancesPage } from "./features/hr/balances/BalancesPage";
import { EmployeesPage } from "./features/hr/employees/EmployeesPage";
import { HolidaysPage } from "./features/hr/holidays/HolidaysPage";
import { AllLeavePage } from "./features/hr/leave/AllLeavePage";
import { MonthlyReportPage } from "./features/hr/report/MonthlyReportPage";
import { SettingsPage } from "./features/hr/settings/SettingsPage";
import { TeamsPage } from "./features/hr/teams/TeamsPage";
import { SampleForm } from "./SampleForm";
import { Layout } from "./components/ui/Layout";

export function AppRoutes() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/requests" element={<MyRequests />} />
        <Route path="/requests/new" element={<NewRequest />} />
        <Route path="/requests/:id" element={<RequestDetail />} />
        <Route path="/calendar" element={<CalendarPage />} />
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
          path="/hr/leave"
          element={
            <RequireHr>
              <AllLeavePage />
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
        <Route
          path="/hr/report"
          element={
            <RequireHr>
              <MonthlyReportPage />
            </RequireHr>
          }
        />
        <Route path="/sign-in" element={<div className="auth card"><SignIn /></div>} />
        <Route path="/set-password" element={<div className="auth card"><SetPassword /></div>} />
        <Route path="/forgot-password" element={<div className="auth card"><ForgotPassword /></div>} />
        <Route path="/reset-password" element={<div className="auth card"><ResetPassword /></div>} />
        <Route path="/account/password" element={<div className="auth card"><ChangePassword /></div>} />
        <Route path="*" element={<h1>Page not found</h1>} />
      </Routes>
    </Layout>
  );
}
