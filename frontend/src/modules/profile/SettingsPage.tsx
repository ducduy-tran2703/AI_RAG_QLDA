import { useState } from 'react';
import { useAdminSettings, useUpdateSetting } from '@/hooks/useAdminSettings';
import { useAuthStore } from '@/stores/authStore';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, List, TabsTrigger } from '@/components/ui/tabs'; // Giả định Tabs component từ shadcn
import { Save, Shield, Mail, Database, Brain, Globe } from 'lucide-react';

export default function SettingsPage() {
  const user = useAuthStore((s) => s.user);
  const { data: settings, isLoading } = useAdminSettings();
  const updateMutation = useUpdateSetting();

  const isAdmin = user?.role === 'IT_ADMIN';

  const handleUpdate = async (key: string, value: string) => {
    try {
      await updateMutation.mutateAsync({ key, value });
      alert('Cập nhật thành công!');
    } catch (e) {
      alert('Lỗi khi cập nhật cấu hình');
    }
  };

  if (!isAdmin) return <div className="p-8">Bạn không có quyền truy cập trang này.</div>;
  if (isLoading) return <div className="p-8 text-center">Đang tải cấu hình...</div>;

  // Group settings by category
  const categories = Array.from(new Set(settings?.map((s: any) => s.category)));

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Cài đặt hệ thống</h2>
        <p className="text-muted-foreground">Quản lý các tham số vận hành của toàn hệ thống</p>
      </div>

      <div className="grid gap-6">
        {settings?.map((setting: any) => (
          <Card key={setting.key}>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">{setting.label}</CardTitle>
              <CardDescription>{setting.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4 items-center">
                <div className="flex-1">
                  <Input
                    defaultValue={setting.value}
                    onBlur={(e) => {
                      if (e.target.value !== setting.value) {
                        handleUpdate(setting.key, e.target.value);
                      }
                    }}
                  />
                </div>
                <Badge variant="outline" className="font-mono text-xs uppercase">{setting.value_type}</Badge>
              </div>
            </CardContent>
          </Card>
        ))}

        {settings?.length === 0 && (
          <div className="text-center py-12 border-2 border-dashed rounded-lg">
            <Settings2 className="mx-auto h-12 w-12 text-muted-foreground opacity-20" />
            <p className="mt-4 text-muted-foreground">Chưa có cấu hình nào trong database.</p>
          </div>
        )}
      </div>
    </div>
  );
}
