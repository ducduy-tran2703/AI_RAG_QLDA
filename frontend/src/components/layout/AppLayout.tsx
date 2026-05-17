import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';

export default function AppLayout() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen">
      {/* Sidebar đơn giản */}
      <aside className="w-64 bg-gray-800 text-white flex flex-col">
        <div className="p-4 font-bold text-lg">AI VanBan</div>
        <nav className="flex-1 p-2">
          <Link to="/dashboard" className="block p-2 hover:bg-gray-700 rounded">📊 Dashboard</Link>
          <Link to="/documents" className="block p-2 hover:bg-gray-700 rounded">📄 Văn bản</Link>
          {user?.role === 'IT_ADMIN' && (
            <Link to="/admin/users" className="block p-2 hover:bg-gray-700 rounded">👥 Quản lý User</Link>
          )}
          {user?.role === 'LEADER' && (
            <Link to="/pending-approvals" className="block p-2 hover:bg-gray-700 rounded">📋 Chờ phê duyệt</Link>
          )}
        </nav>
        <div className="p-4 border-t border-gray-700">
          <p className="text-sm">{user?.full_name}</p>
          <button onClick={handleLogout} className="text-xs text-red-300 mt-1">
            Đăng xuất
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 bg-gray-50 p-6">
        <Outlet />
      </main>
    </div>
  );
}