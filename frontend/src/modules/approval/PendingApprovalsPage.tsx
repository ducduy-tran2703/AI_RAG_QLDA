import { usePendingApprovals, useProcessApproval } from '../../hooks/useApproval';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, XCircle, Clock, FileText, User } from 'lucide-react';

export default function PendingApprovalsPage() {
  const { data: requests, isLoading } = usePendingApprovals();
  const processApproval = useProcessApproval();

  const handleAction = async (requestId: string, action: 'approve' | 'reject') => {
    const note = prompt(`Lý do ${action === 'approve' ? 'duyệt' : 'từ chối'} (nếu có):`);
    try {
      await processApproval.mutateAsync({ requestId, action, note: note || undefined });
      alert('Đã xử lý yêu cầu!');
    } catch (e) {
      alert('Lỗi xử lý yêu cầu');
    }
  };

  if (isLoading) return <div className="p-8 text-center">Đang tải yêu cầu phê duyệt...</div>;

  if (!requests || requests.length === 0) return (
    <div className="p-12 text-center border-2 border-dashed rounded-lg bg-card mt-8">
      <Clock className="mx-auto h-12 w-12 text-muted-foreground opacity-20" />
      <p className="mt-4 text-muted-foreground font-medium">Hiện tại không có yêu cầu nào cần phê duyệt</p>
    </div>
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Văn bản chờ phê duyệt</h2>
        <p className="text-muted-foreground">Danh sách các văn bản chuyên viên đã gửi và đang chờ ý kiến lãnh đạo</p>
      </div>

      <div className="grid gap-4">
        {requests.map((req) => (
          <Card key={req.id} className="overflow-hidden">
            <CardHeader className="bg-muted/30 pb-4">
              <div className="flex justify-between items-start">
                <div className="flex gap-4">
                  <div className="bg-primary/10 p-2 rounded-lg h-fit">
                    <FileText className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">Văn bản: {req.document_name || req.document_id}</CardTitle>
                    <CardDescription className="flex items-center gap-2 mt-1">
                      <Clock className="w-3 h-3" />
                      Gửi lúc: {new Date(req.submitted_at).toLocaleString('vi-VN')}
                    </CardDescription>
                  </div>
                </div>
                <Badge variant="warning">Đang chờ</Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-4 flex flex-col md:flex-row justify-between items-end md:items-center gap-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <User className="w-4 h-4" />
                  Người gửi: <span className="font-medium text-foreground">{req.submitter_name || req.submitted_by}</span>
                </div>
                {req.submitter_note && (
                  <p className="text-sm italic text-muted-foreground bg-muted/50 p-2 rounded">
                    "{req.submitter_note}"
                  </p>
                )}
              </div>

              <div className="flex gap-2">
                <Button variant="outline" className="text-destructive hover:bg-destructive/10" onClick={() => handleAction(req.id, 'reject')}>
                  <XCircle className="w-4 h-4 mr-2" /> Từ chối
                </Button>
                <Button className="bg-green-600 hover:bg-green-700" onClick={() => handleAction(req.id, 'approve')}>
                  <CheckCircle2 className="w-4 h-4 mr-2" /> Phê duyệt
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
