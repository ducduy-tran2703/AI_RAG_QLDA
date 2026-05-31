import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useCreateApproval } from '../../hooks/useApproval';
import { documentApi, adminApi } from '../../lib/api';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Send, ArrowLeft, FileText, User, Loader2 } from 'lucide-react';

export default function SubmitApprovalPage() {
  const [searchParams] = useSearchParams();
  const docId = searchParams.get('docId') || '';
  const checkId = searchParams.get('checkId') || '';

  const [document, setDocument] = useState<any>(null);
  const [leaders, setLeaders] = useState<any[]>([]);
  const [note, setNote] = useState('');
  const [approverId, setApproverId] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const navigate = useNavigate();
  const createApproval = useCreateApproval();

  useEffect(() => {
    const fetchData = async () => {
      if (!docId) {
        navigate('/documents');
        return;
      }
      try {
        const [docRes, leadersRes] = await Promise.all([
          documentApi.get(docId),
          adminApi.listUsers({ role: 'LEADER' })
        ]);
        setDocument(docRes.data);
        setLeaders(leadersRes.data.users);
      } catch (err) {
        console.error('Error fetching data:', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [docId, navigate]);

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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6 py-8">
      <Button variant="ghost" className="mb-2" onClick={() => navigate(-1)}>
        <ArrowLeft className="w-4 h-4 mr-2" /> Quay lại
      </Button>

      <Card className="border-none shadow-lg">
        <CardHeader className="bg-primary/5">
          <div className="flex items-center gap-4">
            <div className="bg-primary p-3 rounded-2xl shadow-sm">
              <Send className="w-6 h-6 text-primary-foreground" />
            </div>
            <div>
              <CardTitle>Gửi văn bản để phê duyệt</CardTitle>
              <CardDescription>Văn bản sẽ được gửi tới lãnh đạo để xem xét và ký duyệt</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6 pt-6">
          <div className="p-4 bg-muted/50 rounded-lg flex items-center gap-4 border">
            <div className="bg-background p-2 rounded-md shadow-sm">
              <FileText className="h-6 w-6 text-muted-foreground" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Tài liệu</p>
              <p className="text-sm font-medium truncate">{document?.display_name || docId}</p>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="approver" className="text-sm font-bold">Người phê duyệt (Lãnh đạo)</Label>
            <Select value={approverId} onValueChange={setApproverId}>
              <SelectTrigger id="approver" className="h-11">
                <SelectValue placeholder="Chọn lãnh đạo phụ trách..." />
              </SelectTrigger>
              <SelectContent>
                {leaders.map((leader) => (
                  <SelectItem key={leader.id} value={leader.id}>
                    <div className="flex items-center gap-2">
                      <User className="h-4 w-4 text-muted-foreground" />
                      <span>{leader.full_name}</span>
                      <span className="text-xs text-muted-foreground">({leader.email})</span>
                    </div>
                  </SelectItem>
                ))}
                {leaders.length === 0 && (
                  <div className="p-2 text-center text-xs text-muted-foreground">Không tìm thấy lãnh đạo nào</div>
                )}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="note" className="text-sm font-bold">Ghi chú cho người duyệt</Label>
            <textarea
              id="note"
              className="w-full min-h-[120px] rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-shadow"
              placeholder="Vui lòng kiểm tra kỹ phần căn lề trang 2 và nội dung tại mục 3..."
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </div>
        </CardContent>
        <CardFooter className="flex justify-between border-t pt-6 bg-muted/5">
          <Button variant="outline" onClick={() => navigate(-1)}>Hủy bỏ</Button>
          <Button onClick={handleSubmit} disabled={!approverId || createApproval.isPending} size="lg">
            {createApproval.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Đang gửi...
              </>
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" /> Gửi phê duyệt ngay
              </>
            )}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
