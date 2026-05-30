import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useRuleSet, useUpdateRule, useDeleteRule, useCreateRule, useUpdateRuleSet } from '@/hooks/useRules';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  ChevronLeft,
  Save,
  Plus,
  Trash2,
  AlertTriangle,
  Settings2,
  CheckCircle2,
  Info
} from 'lucide-react';

export default function RuleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const ruleSetId = Number(id);

  const { data: ruleSet, isLoading } = useRuleSet(ruleSetId);
  const updateRuleMutation = useUpdateRule();
  const deleteRuleMutation = useDeleteRule();

  if (isLoading) return <div className="p-8 text-center">Đang tải dữ liệu bộ quy tắc...</div>;
  if (!ruleSet) return <div className="p-8 text-center text-destructive">Không tìm thấy bộ quy tắc.</div>;

  const handleToggleRule = async (ruleId: string, currentState: boolean) => {
    try {
      await updateRuleMutation.mutateAsync({
        id: ruleId,
        setId: ruleSetId,
        data: { is_active: !currentState }
      });
    } catch (error) {
      alert('Lỗi khi cập nhật quy tắc');
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm('Bạn có chắc chắn muốn xóa quy tắc này?')) return;
    try {
      await deleteRuleMutation.mutateAsync({ id: ruleId, setId: ruleSetId });
    } catch (error) {
      alert('Lỗi khi xóa quy tắc');
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <Badge className="bg-red-500"><AlertTriangle className="w-3 h-3 mr-1" /> Nghiêm trọng</Badge>;
      case 'warning':
        return <Badge className="bg-amber-500 text-white"><Settings2 className="w-3 h-3 mr-1" /> Cảnh báo</Badge>;
      default:
        return <Badge className="bg-blue-500"><Info className="w-3 h-3 mr-1" /> Thông tin</Badge>;
    }
  };

  // Nhóm các quy tắc theo category (font, margin, spacing...)
  const groupedRules = ruleSet.rules.reduce((acc: any, rule: any) => {
    if (!acc[rule.category]) acc[rule.category] = [];
    acc[rule.category].push(rule);
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/rules')}>
          <ChevronLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h2 className="text-3xl font-bold tracking-tight">{ruleSet.name}</h2>
            <Badge variant="outline">{ruleSet.version}</Badge>
          </div>
          <p className="text-muted-foreground">{ruleSet.description || 'Chi tiết các quy tắc kiểm tra'}</p>
        </div>
      </div>

      <div className="grid gap-8">
        {Object.entries(groupedRules).map(([category, rules]: [string, any]) => (
          <div key={category} className="space-y-4">
            <h3 className="text-lg font-bold flex items-center gap-2 border-b pb-2">
              <span className="uppercase text-xs bg-muted px-2 py-1 rounded text-muted-foreground">Nhóm</span>
              {category.toUpperCase()}
            </h3>
            <div className="grid gap-4">
              {rules.map((rule: any) => (
                <Card key={rule.id} className={!rule.is_active ? 'opacity-60 grayscale' : ''}>
                  <CardHeader className="py-4">
                    <div className="flex justify-between items-start">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <CardTitle className="text-base">{rule.name}</CardTitle>
                          {getSeverityBadge(rule.severity)}
                        </div>
                        <CardDescription className="text-xs font-mono">{rule.rule_code}</CardDescription>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant={rule.is_active ? "default" : "outline"}
                          size="sm"
                          onClick={() => handleToggleRule(rule.id, rule.is_active)}
                        >
                          {rule.is_active ? 'Đang bật' : 'Đã tắt'}
                        </Button>
                        <Button variant="ghost" size="icon" className="text-destructive" onClick={() => handleDeleteRule(rule.id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="py-3 border-t bg-muted/10">
                    <div className="grid md:grid-cols-2 gap-6 text-sm">
                      <div>
                        <span className="text-muted-foreground font-medium block mb-2">Giá trị kỳ vọng:</span>
                        <pre className="bg-background p-3 rounded border text-xs overflow-auto">
                          {JSON.stringify(rule.expected_value, null, 2)}
                        </pre>
                      </div>
                      <div className="space-y-4">
                        <div>
                          <span className="text-muted-foreground font-medium block mb-1">Thông báo lỗi:</span>
                          <p className="italic text-muted-foreground">"{rule.error_message}"</p>
                        </div>
                        <div>
                          <span className="text-muted-foreground font-medium block mb-1">Gợi ý sửa:</span>
                          <p className="text-sm">{rule.fix_suggestion || 'Chưa có gợi ý'}</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
              <Button variant="dashed" className="w-full border-2">
                <Plus className="w-4 h-4 mr-2" /> Thêm quy tắc vào nhóm {category}
              </Button>
            </div>
          </div>
        ))}
      </div>

      <div className="flex justify-end gap-2 pt-6 border-t">
        <Button variant="outline" onClick={() => navigate('/rules')}>Quay lại</Button>
        <Button onClick={() => alert('Cấu hình đã được lưu tự động!')}>
          <Save className="w-4 h-4 mr-2" /> Lưu cấu hình
        </Button>
      </div>
    </div>
  );
}