import { useState } from 'react';
import { useAdminUsers, useCreateUser, useLockUser, useUnlockUser, useResetPassword } from '../../hooks/userAdminUsers';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Users, UserPlus, Search, Lock, Unlock, Key, MoreHorizontal, Loader2, Mail, Shield } from 'lucide-react';

export default function AdminUsersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const { data, isLoading, refetch } = useAdminUsers(page, 10, { search });
  const createUser = useCreateUser();
  const lockUser = useLockUser();
  const unlockUser = useUnlockUser();
  const resetPassword = useResetPassword();

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newUser, setNewUser] = useState({ email: '', full_name: '', password: '', role: 'OFFICER' });

  const handleCreate = async () => {
    try {
      await createUser.mutateAsync(newUser);
      setIsCreateOpen(false);
      setNewUser({ email: '', full_name: '', password: '', role: 'OFFICER' });
      refetch();
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Lỗi tạo user');
    }
  };

  const users = data?.users || [];
  const meta = data?.meta || { total: 0, total_pages: 1 };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Quản lý người dùng</h2>
          <p className="text-muted-foreground">Quản lý tài khoản, phân quyền và trạng thái hoạt động của nhân viên</p>
        </div>

        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button className="shrink-0">
              <UserPlus className="w-4 h-4 mr-2" /> Tạo tài khoản mới
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Tạo người dùng mới</DialogTitle>
              <DialogDescription>
                Điền thông tin chi tiết để tạo tài khoản mới trong hệ thống.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" placeholder="email@agency.gov.vn" value={newUser.email} onChange={(e) => setNewUser({...newUser, email: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">Họ và tên</Label>
                <Input id="name" placeholder="Nguyễn Văn A" value={newUser.full_name} onChange={(e) => setNewUser({...newUser, full_name: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Mật khẩu ban đầu</Label>
                <Input id="password" type="password" value={newUser.password} onChange={(e) => setNewUser({...newUser, password: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="role">Vai trò hệ thống</Label>
                <Select value={newUser.role} onValueChange={(v) => setNewUser({...newUser, role: v})}>
                  <SelectTrigger>
                    <SelectValue placeholder="Chọn vai trò" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="OFFICER">Chuyên viên</SelectItem>
                    <SelectItem value="LEADER">Lãnh đạo</SelectItem>
                    <SelectItem value="IT_ADMIN">IT Admin</SelectItem>
                    <SelectItem value="BIZ_ADMIN">Admin nghiệp vụ</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Hủy</Button>
              <Button onClick={handleCreate} disabled={createUser.isPending}>
                {createUser.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Tạo tài khoản'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-3">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Tìm theo tên hoặc email..."
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                className="pl-9"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Người dùng</TableHead>
                  <TableHead>Vai trò</TableHead>
                  <TableHead>Trạng thái</TableHead>
                  <TableHead>Đăng nhập cuối</TableHead>
                  <TableHead className="text-right">Thao tác</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={5} className="h-24 text-center">
                      <Loader2 className="h-6 w-6 animate-spin mx-auto text-primary" />
                    </TableCell>
                  </TableRow>
                ) : users.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                      Không tìm thấy người dùng nào.
                    </TableCell>
                  </TableRow>
                ) : (
                  users.map((user: any) => (
                    <TableRow key={user.id}>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium">{user.full_name}</span>
                          <span className="text-xs text-muted-foreground">{user.email}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="flex w-fit gap-1 items-center">
                          <Shield className="w-3 h-3" />
                          {user.role}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={user.is_active ? 'success' : 'destructive'}>
                          {user.is_active ? 'Hoạt động' : 'Đã khóa'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {user.last_login_at ? new Date(user.last_login_at).toLocaleString('vi-VN', {
                          day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'
                        }) : 'Chưa từng'}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            title={user.is_active ? 'Khóa tài khoản' : 'Mở khóa'}
                            onClick={() => user.is_active ? lockUser.mutate(user.id) : unlockUser.mutate(user.id)}
                          >
                            {user.is_active ? <Lock className="w-4 h-4 text-destructive" /> : <Unlock className="w-4 h-4 text-green-600" />}
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            title="Đặt lại mật khẩu"
                            onClick={async () => {
                              if(confirm('Xác nhận đặt lại mật khẩu cho người dùng này?')) {
                                const res = await resetPassword.mutateAsync(user.id);
                                alert(res.message);
                              }
                            }}
                          >
                            <Key className="w-4 h-4 text-blue-600" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {meta.total_pages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-muted-foreground">
                Tổng cộng {meta.total} người dùng
              </p>
              <div className="flex gap-1">
                <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                  Trước
                </Button>
                <Button variant="outline" size="sm" disabled={page >= meta.total_pages} onClick={() => setPage(page + 1)}>
                  Sau
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}