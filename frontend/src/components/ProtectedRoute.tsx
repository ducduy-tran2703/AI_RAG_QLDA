import { Navigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

interface Props {
  children: React.ReactNode;
}

export default function ProtectedRoute({ children }: Props) {
  const user = useAuthStore((s) => s.user);
  const isInitialized = useAuthStore((s) => s.isInitialized);

  // Đang load user từ token
  if (!isInitialized) {
    return <div className="flex items-center justify-center min-h-screen">Đang tải...</div>;
  }

  // Chưa login → redirect tới login
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Đã login → render component
  return <>{children}</>;
}
