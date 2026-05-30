import { useRuleSets, useCreateRuleSet, useCloneRuleSet } from '@/hooks/useRules';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Gavel, Copy, Plus, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function RuleSetPage() {
  const { data: ruleSets, isLoading } = useRuleSets();
  const cloneMutation = useCloneRuleSet();

  const handleClone = async (id: number, name: string) => {
    const newName = prompt('Nhập tên bộ quy tắc mới:', `${name} (Bản sao)`);
    const newCode = prompt('Nhập mã bộ quy tắc mới (duy nhất):', `${id}_CLONE_${Date.now()}`);

    if (newName && newCode) {
      try {
        await cloneMutation.mutateAsync({ id, data: { new_name: newName, new_code: newCode } });
        alert('Đã sao chép bộ quy tắc!');
      } catch (error) {
        alert('Lỗi khi sao chép');
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Bộ quy tắc kiểm tra</h2>
          <p className="text-muted-foreground">Cấu hình các tiêu chí AI dùng để đánh giá văn bản</p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" /> Tạo bộ quy tắc mới
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {isLoading ? (
          <p>Đang tải...</p>
        ) : (
          ruleSets?.map((set: any) => (
            <Card key={set.id} className={set.is_default ? 'border-primary shadow-md' : ''}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <Gavel className="w-6 h-6 text-primary" />
                  </div>
                  {set.is_default && <Badge>Mặc định</Badge>}
                </div>
                <CardTitle className="mt-4">{set.name}</CardTitle>
                <CardDescription>{set.code}</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                  {set.description || 'Không có mô tả.'}
                </p>
                <div className="flex gap-2 mb-4">
                  {set.doc_types.map((type: string) => (
                    <Badge key={type} variant="outline">{type}</Badge>
                  ))}
                </div>
                <div className="flex justify-between items-center">
                  <div className="text-xs text-muted-foreground">
                    Phiên bản: {set.version}
                  </div>
                  <div className="flex gap-2">
                    <Button variant="ghost" size="icon" onClick={() => handleClone(set.id, set.name)}>
                      <Copy className="w-4 h-4" />
                    </Button>
                    <Button asChild size="sm">
                      <Link to={`/rules/${set.id}`}>
                        Chi tiết <ArrowRight className="w-4 h-4 ml-2" />
                      </Link>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}