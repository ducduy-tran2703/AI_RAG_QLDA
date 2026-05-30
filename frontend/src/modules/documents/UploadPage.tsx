import { useState, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useUploadDocument } from '../../hooks/useDocuments';
import { useCheckProgress } from '../../hooks/useWebSocket';
import { FileUploadZone } from '@/components/ui/FileUploadZone';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { CheckCircle2, Loader2, ArrowRight } from 'lucide-react';

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [checkId, setCheckId] = useState<string | null>(null);
  const [progress, setProgress] = useState({ stage: '', percent: 0 });
  const [complete, setComplete] = useState(false);
  const [resultId, setResultId] = useState<string | null>(null);

  const navigate = useNavigate();
  const uploadMutation = useUploadDocument();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) setFile(acceptedFiles[0]);
  }, []);

  const onRemove = () => setFile(null);

  // Nhận progress từ WebSocket
  useCheckProgress(
    checkId,
    (data) => setProgress({ stage: data.stage, percent: data.percent }),
    (data) => {
      setComplete(true);
      setResultId(data.result_id);
      setProgress({ stage: 'done', percent: 100 });
    }
  );

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await uploadMutation.mutateAsync(formData);
      setCheckId(res.check_id);
    } catch (err) {
      alert('Upload thất bại');
      setUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Kiểm tra văn bản mới</h2>
        <p className="text-muted-foreground">Tải lên văn bản hành chính để AI phân tích và phát hiện lỗi thể thức</p>
      </div>

      <Card>
        <CardContent className="pt-6">
          {!checkId ? (
            <div className="space-y-6">
              <FileUploadZone
                onDrop={onDrop}
                files={file ? [file] : []}
                onRemove={onRemove}
                accept={{
                  'application/pdf': ['.pdf'],
                  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
                }}
                multiple={false}
              />

              <div className="flex gap-2 justify-end">
                <Button variant="ghost" onClick={() => navigate('/documents')}>Hủy</Button>
                <Button onClick={handleUpload} disabled={!file || uploading}>
                  {uploading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Đang tải lên...
                    </>
                  ) : 'Bắt đầu kiểm tra'}
                </Button>
              </div>
            </div>
          ) : (
            <div className="py-8 space-y-6 text-center">
              <div className="space-y-2">
                <h3 className="text-xl font-semibold">
                  {complete ? 'Kiểm tra hoàn tất!' : 'Đang phân tích văn bản...'}
                </h3>
                <p className="text-sm text-muted-foreground">
                  {progress.stage === 'done' ? 'Hệ thống đã xử lý xong' : `Giai đoạn: ${progress.stage}`}
                </p>
              </div>

              <div className="px-12">
                <Progress value={progress.percent} className="h-3" />
                <p className="text-xs mt-2 text-muted-foreground font-mono">{progress.percent}%</p>
              </div>

              {complete && resultId ? (
                <div className="pt-4 animate-in fade-in zoom-in duration-500">
                  <div className="bg-green-50 text-green-700 p-4 rounded-lg flex items-center justify-center gap-2 mb-6">
                    <CheckCircle2 className="h-5 w-5" />
                    <span className="font-medium">AI đã hoàn thành báo cáo lỗi cho văn bản của bạn</span>
                  </div>
                  <Button size="lg" className="w-full" asChild>
                    <Link to={`/checks/${resultId}`}>
                      Xem kết quả chi tiết <ArrowRight className="ml-2 h-4 w-4" />
                    </Link>
                  </Button>
                </div>
              ) : (
                <div className="grid grid-cols-4 gap-2 px-12">
                  {[30, 65, 90, 100].map((step, idx) => (
                    <div
                      key={idx}
                      className={`h-1 rounded-full ${progress.percent >= step ? 'bg-primary' : 'bg-muted'}`}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
