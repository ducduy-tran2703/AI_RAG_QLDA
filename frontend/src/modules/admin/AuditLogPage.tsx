import { useState } from 'react';
import { useAuditLogs } from '@/hooks/useAdminSettings';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Search, History } from 'lucide-react';
import { Input } from '@/components/ui/input';

export default function AuditLogPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useAuditLogs(page, 20);

  const logs = data?.logs || [];
  const meta = data?.meta || { total: 0 };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Nhật ký hệ thống (Audit Logs)</h2>
          <p className="text-muted-foreground">Theo dõi và truy vết hoạt động của người dùng</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <div className="relative w-64">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Tìm kiếm hành động..." className="pl-8" />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 border-b">
                <tr>
                  <th className="h-10 px-4 text-left font-medium">Thời gian</th>
                  <th className="h-10 px-4 text-left font-medium">Tác nhân</th>
                  <th className="h-10 px-4 text-left font-medium">Hành động</th>
                  <th className="h-10 px-4 text-left font-medium">Tài nguyên</th>
                  <th className="h-10 px-4 text-center font-medium">Kết quả</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {isLoading ? (
                  <tr><td colSpan={5} className="h-24 text-center">Đang tải nhật ký...</td></tr>
                ) : logs.length === 0 ? (
                  <tr><td colSpan={5} className="h-24 text-center text-muted-foreground">Chưa có bản ghi nào</td></tr>
                ) : (
                  logs.map((log: any) => (
                    <tr key={log.id} className="hover:bg-muted/50 transition-colors">
                      <td className="p-4">{new Date(log.created_at).toLocaleString('vi-VN')}</td>
                      <td className="p-4">
                        <div className="flex flex-col">
                          <span className="font-medium text-xs uppercase">{log.actor_type}</span>
                          <span className="text-muted-foreground text-[10px]">{log.user_id || 'SYSTEM'}</span>
                        </div>
                      </td>
                      <td className="p-4 font-medium">{log.action}</td>
                      <td className="p-4">
                        <Badge variant="outline">{log.resource_type}</Badge>
                      </td>
                      <td className="p-4 text-center">
                        <Badge variant={log.result === 'success' ? 'default' : 'destructive'} className="uppercase text-[10px]">
                          {log.result}
                        </Badge>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="flex justify-between items-center mt-4">
            <div className="text-xs text-muted-foreground">Tổng số: {meta.total} bản ghi</div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(1, p-1))} disabled={page === 1}>Trước</Button>
              <Button variant="outline" size="sm" onClick={() => setPage(p => p + 1)}>Sau</Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
