import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useCreateApproval } from '../../hooks/useApproval';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea'; // Giả định Textarea component
import { Input } from '@/components/ui/input';
import { Send, ArrowLeft, FileText, Search } from 'lucide-react';

export default function SubmitApprovalPage() {
  const [searchParams] = useSearchParams();
  const docId = searchParams.get('docId') || '';
  const checkId = searchParams.get('checkId') || '';
  const [note, setNote] = useState('');
  const [approverId, setApproverId] = useState('');
  const navigate = useNavigate();
  const createApproval = useCreateApproval();

  const handleSubmit = async () => {
    if (!docId || !approverId) return alert('Vui lòng chọn người phê duyệt');

    try {
      await createApproval.mutateAsync({
        document_id: docId,
        approver_id: approverId,
        note,
        check_result_id: checkId || undefined,
      });
      alert('Đã gửi phê duyệt thành công!');
      navigate('/documents');
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Lỗi gửi phê duyệt');
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <Button variant="ghost" className="mb-2" onClick={() => navigate(-1)}>
        <ArrowLeft className="w-4 h-4 mr-2" /> Quay lại
      </Button>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <div className="bg-primary/10 p-3 rounded-full">
              <Send className="w-6 h-6 text-primary" />
            </div>
            <div>
              <CardTitle>Gửi văn bản để phê duyệt</CardTitle>
              <CardDescription>Văn bản sẽ được gửi tới lãnh đạo để xem xét và ký duyệt</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-4 bg-muted/50 rounded-lg flex items-center gap-3">
            <FileText className="text-muted-foreground" />
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase">Tài liệu</p>
              <p className="text-sm font-mono">{docId}</p>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="approver">ID Người phê duyệt (Lãnh đạo)</Label>
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                id="approver"
                placeholder="Nhập mã định danh lãnh đạo..."
                className="pl-10"
                value={approverId}
                onChange={(e) => setApproverId(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="note">Ghi chú cho người duyệt</Label>
            <textarea
              id="note"
              className="w-full min-h-[120px] rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              placeholder="Vui lòng kiểm tra kỹ phần căn lề trang 2..."
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </div>
        </CardContent>
        <CardFooter className="flex justify-between border-t pt-6 bg-muted/10">
          <Button variant="outline" onClick={() => navigate(-1)}>Hủy bỏ</Button>
          <Button onClick={handleSubmit} disabled={!approverId}>
            <Send className="w-4 h-4 mr-2" /> Gửi phê duyệt ngay
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
