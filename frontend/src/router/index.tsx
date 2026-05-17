import { createBrowserRouter, Navigate } from 'react-router-dom';
import LoginPage from '../modules/auth/LoginPage';
import DocumentListPage from '../modules/documents/DocumentListPage';
import UploadPage from '../modules/documents/UploadPage';
import CheckResultPage from '../modules/checks/CheckResultPage';
import DashboardPage from '../modules/analytics/DashboardPage';
import AdminUsersPage from '../modules/admin/AdminUsersPage';
import SubmitApprovalPage from '../modules/approval/SubmitApprovalPage';
import PendingApprovalsPage from '../modules/approval/PendingApprovalsPage';
import ProfilePage from '../modules/profile/ProfilePage';
import SettingsPage from '../modules/profile/SettingsPage';
import ModernLayout from '../components/layout/ModernLayout';
import ProtectedRoute from '../components/ProtectedRoute';

const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <ModernLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/documents" replace />,
      },
      {
        path: 'documents',
        element: <DocumentListPage />,
      },
      {
        path: 'upload',
        element: <UploadPage />,
      },
      {
        path: 'checks/:id',
        element: <CheckResultPage />,
      },
      {
        path: 'dashboard',
        element: <DashboardPage />,
      },
      {
        path: 'admin/users',
        element: <AdminUsersPage />,
      },
      {
        path: 'submit-approval',
        element: <SubmitApprovalPage />,
      },
      {
        path: 'pending-approvals',
        element: <PendingApprovalsPage />,
      },
      {
        path: 'profile',
        element: <ProfilePage />,
      },
      {
        path: 'settings',
        element: <SettingsPage />,
      },
    ],
  },
]);

export default router;