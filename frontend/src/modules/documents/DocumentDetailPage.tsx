import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentApi, checkApi } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  ArrowLeft, FileText, Download, Trash2, RotateCcw,
  ExternalLink, Calendar, HardDrive, Tag, FolderOpen,
  Clock, History, CheckCircle2, AlertCircle, Loader2, Upload
} from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea'; // Giả định component tồn tại hoặc dùng textarea chuẩn

const formatDate = (dateString: string) => {
  try {
    const date = new Date(dateString);
    return date.toLocaleString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (e) {
    return dateString;
  }
};

export default function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isRechecking, setIsRechecking] = useState(false);

  // States cho upload phiên bản mới
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [changeNotes, setChangeNotes] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  const { data: doc, isLoading: isDocLoading, error } = useQuery({
    queryKey: ['document', id],
    queryFn: async () => {
      const res = await documentApi.get(id!);
      return res.data;
    },
    enabled: !!id,
  });

  const { data: versions, isLoading: isVersionsLoading } = useQuery({
    queryKey: ['document-versions', id],
    queryFn: async () => {
      const res = await documentApi.listVersions(id!);
      return res.data;
    },
    enabled: !!id,
  });

  const { data: checks, isLoading: isChecksLoading } = useQuery({
    queryKey: ['document-checks', id],
    queryFn: async () => {
      const res = await checkApi.listByDocument(id!);
      return res.data;
    },
    enabled: !!id,
  });

  const handleDownload = async () => {
    try {
      const res = await documentApi.download(id!);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', doc.original_filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download error:', err);
      alert('Lỗi khi tải xuống văn bản');
    }
  };

  const handleRecheck = async () => {
    setIsRechecking(true);
    try {
      await checkApi.create(id!);
      alert('Đã bắt đầu kiểm tra lại. Vui lòng đợi trong giây lát.');
      queryClient.invalidateQueries({ queryKey: ['document-checks', id] });
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Lỗi khi yêu cầu kiểm tra lại');
    } finally {
      setIsRechecking(false);
    }
  };

  const handleUploadVersion = async () => {
    if (!uploadFile || !id) return;
    setIsUploading(true);
    try {
      await documentApi.createVersion(id, uploadFile, changeNotes);
      setIsUploadOpen(false);
      setUploadFile(null);
      setChangeNotes('');
      alert('Tải lên phiên bản mới thành công!');
      queryClient.invalidateQueries({ queryKey: ['document-versions', id] });
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Lỗi khi tải lên phiên bản mới');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async () => {
    if (confirm('Bạn có chắc chắn muốn xóa văn bản này?')) {
      try {
        await documentApi.delete(id!);
        navigate('/documents');
      } catch (err: any) {
        alert(err.response?.data?.detail || 'Lỗi khi xóa văn bản');
      }
    }
  };

  if (isDocLoading) return (
    <div className="flex items-center justify-center min-h-[400px]">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
    </div>
  );

  if (error || !doc) return (
    <div className="p-8 text-center space-y-4">
      <AlertCircle className="h-12 w-12 text-destructive mx-auto" />
      <h3 className="text-xl font-bold">Không tìm thấy tài liệu</h3>
      <Button onClick={() => navigate('/documents')}>Quay lại danh sách</Button>
    </div>
  );

  return (
    <div className="space-y-6 max-w-6xl mx-auto py-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/documents')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">{doc.display_name}</h1>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="outline" className="uppercase">{doc.file_type}</Badge>
              <span className="text-sm text-muted-foreground">ID: {doc.id}</span>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleDownload}>
            <Download className="w-4 h-4 mr-2" /> Tải về
          </Button>
          <Button onClick={handleRecheck} disabled={isRechecking}>
            {isRechecking ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <RotateCcw className="w-4 h-4 mr-2" />
            )}
            Kiểm tra lại
          </Button>
          <Button variant="destructive" onClick={handleDelete}>
            <Trash2 className="w-4 h-4 mr-2" /> Xóa
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Info & Stats */}
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-bold uppercase tracking-wider text-muted-foreground">Thông tin chung</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="flex items-center justify-between text-sm">
                <div className="flex items-center text-muted-foreground">
                  <Calendar className="w-4 h-4 mr-2" /> Ngày tạo
                </div>
                <span>{formatDate(doc.created_at)}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center text-muted-foreground">
                  <HardDrive className="w-4 h-4 mr-2" /> Dung lượng
                </div>
                <span>{(doc.file_size_bytes / 1024).toFixed(1)} KB</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center text-muted-foreground">
                  <FolderOpen className="w-4 h-4 mr-2" /> Thư mục
                </div>
                <span>{doc.folder_id || 'Mặc định'}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center text-muted-foreground">
                  <Tag className="w-4 h-4 mr-2" /> Loại văn bản
                </div>
                <Badge variant="secondary">{doc.doc_type || 'Chưa xác định'}</Badge>
              </div>
            </CardContent>
          </Card>

          {doc.latest_check_id && (
            <Card className="border-primary/20 bg-primary/5">
              <CardHeader>
                <CardTitle className="text-sm font-bold uppercase tracking-wider text-primary">Kết quả gần nhất</CardTitle>
              </CardHeader>
              <CardContent className="text-center pb-6">
                <div className={`text-5xl font-bold mb-2 ${
                  (doc.latest_score || 0) >= 75 ? 'text-green-600' : 'text-amber-600'
                }`}>
                  {doc.latest_score ?? '--'}
                </div>
                <p className="text-xs text-muted-foreground mb-4">Điểm tuân thủ thể thức</p>
                <Button className="w-full" asChild>
                  <Link to={`/checks/${doc.latest_check_id}`}>Xem báo cáo chi tiết</Link>
                </Button>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Column: Versions & History */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Lịch sử kiểm tra</CardTitle>
                  <CardDescription>Các phiên kiểm tra đã thực hiện trên văn bản này</CardDescription>
                </div>
                <History className="w-5 h-5 text-muted-foreground" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {isChecksLoading ? (
                  <div className="flex justify-center py-4"><Loader2 className="animate-spin" /></div>
                ) : checks?.length === 0 ? (
                  <p className="text-center text-muted-foreground py-4">Chưa có phiên kiểm tra nào.</p>
                ) : (
                  checks?.map((check: any) => (
                    <div key={check.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-full ${check.status === 'completed' ? 'bg-green-100' : 'bg-blue-100'}`}>
                          {check.status === 'completed' ? (
                            <CheckCircle2 className={`h-4 w-4 ${check.score >= 75 ? 'text-green-600' : 'text-amber-600'}`} />
                          ) : (
                            <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
                          )}
                        </div>
                        <div>
                          <p className="text-sm font-medium">Phiên kiểm tra {formatDate(check.checked_at)}</p>
                          <p className="text-xs text-muted-foreground">Model: {check.ai_model || 'Standard'}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className={`text-lg font-bold ${
                            check.score >= 75 ? 'text-green-600' : 'text-amber-600'
                          }`}>{check.score}</p>
                        </div>
                        <Button variant="ghost" size="sm" asChild>
                          <Link to={`/checks/${check.id}`}>Chi tiết</Link>
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Các phiên bản file</CardTitle>
                  <CardDescription>Danh sách các tệp tin đã tải lên cho tài liệu này</CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <Dialog open={isUploadOpen} onOpenChange={setIsUploadOpen}>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="sm">
                        <Upload className="w-4 h-4 mr-2" /> Tải phiên bản mới
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Tải lên phiên bản mới</DialogTitle>
                        <DialogDescription>Chọn tệp tin để cập nhật cho văn bản hiện tại.</DialogDescription>
                      </DialogHeader>
                      <div className="space-y-4 py-4">
                        <div className="space-y-2">
                          <Label htmlFor="file">Chọn file (.docx, .pdf)</Label>
                          <Input
                            id="file"
                            type="file"
                            accept=".docx,.pdf"
                            onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="notes">Ghi chú thay đổi</Label>
                          <textarea
                            id="notes"
                            className="w-full min-h-[80px] rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                            placeholder="Mô tả ngắn gọn các thay đổi trong phiên bản này..."
                            value={changeNotes}
                            onChange={(e) => setChangeNotes(e.target.value)}
                          />
                        </div>
                      </div>
                      <DialogFooter>
                        <Button variant="outline" onClick={() => setIsUploadOpen(false)}>Hủy</Button>
                        <Button onClick={handleUploadVersion} disabled={!uploadFile || isUploading}>
                          {isUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Tải lên ngay'}
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                  <FileText className="w-5 h-5 text-muted-foreground" />
                </div>
              </div>
            </CardHeader>
            <CardContent>
               <div className="space-y-4">
                {isVersionsLoading ? (
                  <div className="flex justify-center py-4"><Loader2 className="animate-spin" /></div>
                ) : versions?.length === 0 ? (
                   <p className="text-center text-muted-foreground py-4">Duy nhất phiên bản gốc.</p>
                ) : (
                  versions?.map((v: any) => (
                    <div key={v.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <FileText className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <p className="text-sm font-medium">Phiên bản {v.version_number} ({v.version_label})</p>
                          <p className="text-xs text-muted-foreground">
                            {formatDate(v.created_at)} • {(v.file_size_bytes / 1024).toFixed(1)} KB
                          </p>
                        </div>
                      </div>
                      <Button variant="ghost" size="icon">
                        <Download className="h-4 w-4" />
                      </Button>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}