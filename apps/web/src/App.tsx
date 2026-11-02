import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./layouts/AppLayout";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { CreateCampaignPage } from "./pages/CreateCampaignPage";
import { WorkflowPage } from "./pages/WorkflowPage";
import { ResultsPage } from "./pages/ResultsPage";
import { CustomerDetailPage } from "./pages/CustomerDetailPage";
import { CustomersPage } from "./pages/CustomersPage";
import { CustomerBrowseDetailPage } from "./pages/CustomerBrowseDetailPage";
import { useAuth } from "./features/auth/useAuth";

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { token } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <AppLayout />
          </PrivateRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="customers" element={<CustomersPage />} />
        <Route path="customers/:customerId" element={<CustomerBrowseDetailPage />} />
        <Route path="campaigns/new" element={<CreateCampaignPage />} />
        <Route path="campaigns/:campaignId/workflow/:workflowId" element={<WorkflowPage />} />
        <Route path="campaigns/:campaignId/results" element={<ResultsPage />} />
        <Route
          path="campaigns/:campaignId/customers/:customerId"
          element={<CustomerDetailPage />}
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
