import { useState } from 'react';
import { useAdminUsers, useCreateUser, useLockUser, useUnlockUser, useResetPassword } from '../../hooks/userAdminUsers';

export default function AdminUsersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const { data } = useAdminUsers(page, 10, { search });
  const createUser = useCreateUser();
  const lockUser = useLockUser();
  const unlockUser = useUnlockUser();
  const resetPassword = useResetPassword();

  const [showCreate, setShowCreate] = useState(false);
  const [newUser, setNewUser] = useState({ email: '', full_name: '', password: '', role: 'OFFICER' });

  const handleCreate = async () => {
    try {
      await createUser.mutateAsync(newUser);
      setShowCreate(false);
      setNewUser({ email: '', full_name: '', password: '', role: 'OFFICER' });
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Lỗi tạo user');
    }
  };

  const handleLock = async (userId: string) => {
    await lockUser.mutateAsync(userId);
  };
  const handleUnlock = async (userId: string) => {
    await unlockUser.mutateAsync(userId);
  };
  const handleResetPw = async (userId: string) => {
    const res = await resetPassword.mutateAsync(userId);
    alert(res.message);
  };

  const users = data?.users || [];
  const meta = data?.meta || { total: 0 };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Quản lý người dùng ({meta.total})</h2>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          + Tạo tài khoản
        </button>
      </div>

      <div className="mb-4">
        <input
          type="text"
          placeholder="Tìm kiếm email hoặc tên..."
          className="border rounded p-2 w-64"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
        />
      </div>

      {showCreate && (
        <div className="bg-gray-50 p-4 rounded mb-4">
          <h3 className="font-semibold mb-2">Tạo người dùng mới</h3>
          <div className="grid grid-cols-2 gap-4">
            <input placeholder="Email" className="border p-2 rounded" value={newUser.email} onChange={(e) => setNewUser({...newUser, email: e.target.value})} />
            <input placeholder="Họ tên" className="border p-2 rounded" value={newUser.full_name} onChange={(e) => setNewUser({...newUser, full_name: e.target.value})} />
            <input placeholder="Mật khẩu" type="password" className="border p-2 rounded" value={newUser.password} onChange={(e) => setNewUser({...newUser, password: e.target.value})} />
            <select className="border p-2 rounded" value={newUser.role} onChange={(e) => setNewUser({...newUser, role: e.target.value})}>
              <option value="OFFICER">Chuyên viên</option>
              <option value="LEADER">Lãnh đạo</option>
              <option value="IT_ADMIN">IT Admin</option>
              <option value="BIZ_ADMIN">Admin nghiệp vụ</option>
            </select>
          </div>
          <button onClick={handleCreate} className="mt-4 bg-green-600 text-white px-4 py-2 rounded">Lưu</button>
          <button onClick={() => setShowCreate(false)} className="ml-2 text-gray-500">Hủy</button>
        </div>
      )}

      <div className="bg-white shadow rounded overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr className="border-b bg-gray-50">
              <th className="text-left p-3">Email</th>
              <th className="text-left p-3">Họ tên</th>
              <th className="text-left p-3">Vai trò</th>
              <th className="text-left p-3">Trạng thái</th>
              <th className="text-left p-3">Đăng nhập cuối</th>
              <th className="text-left p-3">Hành động</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user: any) => (
              <tr key={user.id} className="border-b">
                <td className="p-3">{user.email}</td>
                <td className="p-3">{user.full_name}</td>
                <td className="p-3">{user.role}</td>
                <td className="p-3">{user.is_active ? '🟢 Hoạt động' : '🔴 Khóa'}</td>
                <td className="p-3">{user.last_login_at ? new Date(user.last_login_at).toLocaleString('vi-VN') : '-'}</td>
                <td className="p-3 space-x-2">
                  {user.is_active ? (
                    <button onClick={() => handleLock(user.id)} className="text-red-600 hover:underline">Khóa</button>
                  ) : (
                    <button onClick={() => handleUnlock(user.id)} className="text-green-600 hover:underline">Mở khóa</button>
                  )}
                  <button onClick={() => handleResetPw(user.id)} className="text-blue-600 hover:underline">Đặt lại MK</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {users.length === 0 && <div className="p-4 text-center text-gray-500">Không có người dùng nào</div>}
      </div>

      <div className="flex justify-between items-center mt-4">
        <button onClick={() => setPage(p => Math.max(1, p-1))} disabled={page === 1} className="px-4 py-2 border rounded disabled:opacity-50">← Trước</button>
        <span>Trang {page}</span>
        <button onClick={() => setPage(p => p+1)} className="px-4 py-2 border rounded">Sau →</button>
      </div>
    </div>
  );
}