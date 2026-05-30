import { useState } from 'react';
import { useApiKeys, useCreateApiKey, useRevokeApiKey } from '@/hooks/useApiKeys';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Key, Plus, Trash2, Copy, ShieldCheck, AlertCircle } from 'lucide-react';

export default function DeveloperPortal() {
  const { data: keys, isLoading } = useApiKeys();
  const createMutation = useCreateApiKey();
  const revokeMutation = useRevokeApiKey();
  const [newKeyRaw, setNewKeyRaw] = useState<string | null>(null);

  const handleCreate = async () => {
    const name = prompt('Nhập tên ứng dụng tích hợp:');
    if (!name) return;
    try {
      const res = await createMutation.mutateAsync({ name });
      setNewKeyRaw(res.key);
    } catch (e) {
      alert('Lỗi tạo API Key');
    }
  };

  const handleRevoke = async (id: string) => {
    if (!confirm('Bạn có chắc chắn muốn thu hồi khóa này?')) return;
    await revokeMutation.mutateAsync(id);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Cổng tích hợp API</h2>
          <p className="text-muted-foreground">Quản lý khóa truy cập cho các hệ thống bên thứ 3</p>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="w-4 h-4 mr-2" /> Tạo API Key mới
        </Button>
      </div>

      {newKeyRaw && (
        <Card className="bg-amber-50 border-amber-200">
          <CardHeader>
            <CardTitle className="text-amber-800 flex items-center gap-2">
              <AlertCircle className="h-5 w-5" /> Khóa API mới của bạn
            </CardTitle>
            <CardDescription className="text-amber-700">
              Vui lòng sao chép và lưu trữ khóa này ở nơi an toàn. Bạn sẽ không thể thấy lại nó sau khi đóng thông báo này.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2 items-center bg-white p-3 rounded border border-amber-300">
              <code className="flex-1 font-mono font-bold text-lg">{newKeyRaw}</code>
              <Button size="icon" variant="ghost" onClick={() => { navigator.clipboard.writeText(newKeyRaw); alert('Đã sao chép!'); }}>
                <Copy className="h-4 w-4" />
              </Button>
            </div>
            <Button variant="outline" className="mt-4 border-amber-300 text-amber-800" onClick={() => setNewKeyRaw(null)}>
              Tôi đã lưu, đóng thông báo
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4">
        {isLoading ? (
          <p>Đang tải danh sách khóa...</p>
        ) : keys?.length === 0 ? (
          <div className="text-center py-12 border-2 border-dashed rounded-lg bg-card">
            <Key className="mx-auto h-12 w-12 text-muted-foreground opacity-20" />
            <p className="mt-4 text-muted-foreground">Bạn chưa có API Key nào.</p>
          </div>
        ) : (
          keys?.map((key: any) => (
            <Card key={key.id} className={!key.is_active ? 'opacity-50 grayscale' : ''}>
              <CardContent className="py-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-2 bg-primary/10 rounded-full text-primary">
                    <ShieldCheck className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="font-bold">{key.name}</h3>
                    <p className="text-sm font-mono text-muted-foreground">Prefix: {key.key_prefix}****</p>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground uppercase">Sử dụng</p>
                    <p className="font-bold">{key.usage_count} lần</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground uppercase">Trạng thái</p>
                    <Badge variant={key.is_active ? 'default' : 'secondary'}>
                      {key.is_active ? 'Đang hoạt động' : 'Đã thu hồi'}
                    </Badge>
                  </div>
                  {key.is_active && (
                    <Button variant="ghost" size="icon" className="text-destructive" onClick={() => handleRevoke(key.id)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
