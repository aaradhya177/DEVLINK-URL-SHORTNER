import { createBrowserRouter, Navigate } from "react-router-dom";
import { App } from "../App";
import { AppLayout } from "../layout/AppLayout";
import { AnalyticsPage } from "../features/analytics/AnalyticsPage";
import { LoginPage } from "../features/auth/LoginPage";
import { ProtectedRoute } from "../features/auth/ProtectedRoute";
import { RegisterPage } from "../features/auth/RegisterPage";
import { BulkShortenPage } from "../features/links/BulkShortenPage";
import { LinksDashboardPage } from "../features/links/LinksDashboardPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <Navigate to="/links" replace /> },
      { path: "login", element: <LoginPage /> },
      { path: "register", element: <RegisterPage /> },
      {
        element: <ProtectedRoute />,
        children: [
          {
            element: <AppLayout />,
            children: [
              { path: "links", element: <LinksDashboardPage /> },
              { path: "bulk", element: <BulkShortenPage /> },
              { path: "analytics/:linkId", element: <AnalyticsPage /> },
            ],
          },
        ],
      },
    ],
  },
]);
