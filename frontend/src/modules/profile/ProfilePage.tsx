import { useState, useEffect } from 'react';
import { authApi } from '../../lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { User, Mail, Building, Briefcase, Phone, Globe, Shield, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';

export default function ProfilePage() {
  const [profile, setProfile] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const user = useAuthStore((s) => s.user);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await authApi.getProfile();
        setProfile(res.data);
      } catch (err: any) {
        setError('Không thể tải thông tin hồ sơ.');
      } finally {
        setIsLoading(false);
      }
    };
    fetchProfile();
  }, []);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setIsSaving(true);
    try {
      const { full_name, phone, position, timezone, language } = profile;
      const res = await authApi.updateProfile({ full_name, phone, position, timezone, language });
      setProfile(res.data);
      setSuccess('Cập nhật hồ sơ thành công.');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Không thể cập nhật hồ sơ.');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="container max-w-4xl mx-auto py-8 space-y-6">
      <div className="flex flex-col md:flex-row gap-6 items-start">
        {/* Left column: Avatar & Quick Info */}
        <Card className="w-full md:w-1/3">
          <CardHeader className="text-center">
            <div className="flex justify-center mb-4">
              <Avatar className="h-24 w-24 border-2 border-primary/10">
                <AvatarImage src={profile?.avatar_url} />
                <AvatarFallback className="text-2xl bg-primary/5 text-primary">
                  {profile?.full_name?.charAt(0) || 'U'}
                </AvatarFallback>
              </Avatar>
            </div>
            <CardTitle>{profile?.full_name}</CardTitle>
            <CardDescription>{profile?.email}</CardDescription>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              <Badge variant="secondary" className="bg-primary/10 text-primary hover:bg-primary/20">
                <Shield className="w-3 h-3 mr-1" />
                {profile?.role}
              </Badge>
              {profile?.department && (
                <Badge variant="outline">
                  <Building className="w-3 h-3 mr-1" />
                  {profile.department.name}
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4 pt-4 border-t">
            <div className="flex items-center text-sm">
              <Mail className="w-4 h-4 mr-3 text-muted-foreground" />
              <span>{profile?.email}</span>
            </div>
            <div className="flex items-center text-sm">
              <Briefcase className="w-4 h-4 mr-3 text-muted-foreground" />
              <span>{profile?.position || 'Chưa cập nhật chức danh'}</span>
            </div>
            <div className="flex items-center text-sm">
              <Phone className="w-4 h-4 mr-3 text-muted-foreground" />
              <span>{profile?.phone || 'Chưa cập nhật SĐT'}</span>
            </div>
          </CardContent>
        </Card>

        {/* Right column: Edit Form */}
        <Card className="flex-1">
          <CardHeader>
            <CardTitle>Thông tin chi tiết</CardTitle>
            <CardDescription>Cập nhật thông tin cá nhân của bạn</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleUpdate} className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
              {success && (
                <Alert className="border-green-500 bg-green-50 text-green-700">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <AlertDescription>{success}</AlertDescription>
                </Alert>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="full_name">Họ và tên</Label>
                  <Input
                    id="full_name"
                    value={profile?.full_name || ''}
                    onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
                    placeholder="Nguyễn Văn A"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Số điện thoại</Label>
                  <Input
                    id="phone"
                    value={profile?.phone || ''}
                    onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                    placeholder="09xx xxx xxx"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="position">Chức vụ / Vị trí</Label>
                  <Input
                    id="position"
                    value={profile?.position || ''}
                    onChange={(e) => setProfile({ ...profile, position: e.target.value })}
                    placeholder="Chuyên viên"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="department">Phòng ban</Label>
                  <Input
                    id="department"
                    value={profile?.department?.name || ''}
                    disabled
                    className="bg-muted"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="language">Ngôn ngữ</Label>
                  <Input
                    id="language"
                    value={profile?.language || 'vi'}
                    onChange={(e) => setProfile({ ...profile, language: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="timezone">Múi giờ</Label>
                  <Input
                    id="timezone"
                    value={profile?.timezone || 'Asia/Ho_Chi_Minh'}
                    onChange={(e) => setProfile({ ...profile, timezone: e.target.value })}
                  />
                </div>
              </div>

              <div className="pt-4 flex justify-end">
                <Button type="submit" disabled={isSaving}>
                  {isSaving ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Đang lưu...
                    </>
                  ) : 'Lưu thay đổi'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
