import { useState } from 'react';
import { Outlet, Link, useLocation, useNavigate, Navigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Menu,
  LogOut,
  User,
  Settings,
  FileText,
  LayoutDashboard,
  ChevronLeft,
  Users, ClipboardList,
  History, Key,
} from 'lucide-react';
import { Database, Gavel } from 'lucide-react';
import NotificationBell from './NotificationBell';


const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, roles: ['OFFICER', 'LEADER', 'IT_ADMIN', 'BIZ_ADMIN'] },
  { name: 'Văn bản', href: '/documents', icon: FileText, roles: ['OFFICER', 'LEADER', 'IT_ADMIN', 'BIZ_ADMIN'] },
  { name: 'Chờ phê duyệt', href: '/pending-approvals', icon: ClipboardList, roles: ['LEADER'] },
  { name: 'Quản lý User', href: '/admin/users', icon: Users, roles: ['IT_ADMIN'] },
  { name: 'Nhật ký hệ thống', href: '/admin/audit-logs', icon: History, roles: ['IT_ADMIN'] },
  { name: 'Cổng API', href: '/developer', icon: Key, roles: ['IT_ADMIN', 'BIZ_ADMIN'] },
  { name: 'Cơ sở tri thức', href: '/knowledge', icon: Database, roles: ['BIZ_ADMIN', 'IT_ADMIN'] },
  { name: 'Bộ quy tắc', href: '/rules', icon: Gavel, roles: ['BIZ_ADMIN', 'IT_ADMIN'] },
];

export default function ModernLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  // Fallback: redirect to login if user is somehow null
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const allowedNav = navigation.filter(item => item.roles.includes(user?.role || ''));

  const NavItems = () => (
    <nav className="space-y-1 px-2">
      {allowedNav.map((item) => {
        const isActive = location.pathname.startsWith(item.href);
        const Icon = item.icon;
        return (
          <Tooltip key={item.name}>
            <TooltipTrigger asChild>
              <Link
                to={item.href}
                onClick={() => setSidebarOpen(false)}
                className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                }`}
              >
                <Icon className="h-4 w-4" />
                {item.name}
              </Link>
            </TooltipTrigger>
            <TooltipContent side="right" className="lg:hidden">
              {item.name}
            </TooltipContent>
          </Tooltip>
        );
      })}
    </nav>
  );

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar cho desktop */}
      <aside className="hidden lg:flex lg:w-64 lg:flex-col border-r bg-card">
        <div className="flex items-center h-16 px-4 border-b">
          <Link to="/" className="flex items-center gap-2 font-semibold text-lg">
            <FileText className="h-6 w-6 text-primary" />
            <span>AI Văn bản</span>
          </Link>
        </div>
        <div className="flex-1 overflow-y-auto py-4">
          <NavItems />
        </div>
        <Separator />
        <div className="p-4">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="w-full justify-start gap-2 px-2">
                <Avatar className="h-8 w-8">
                  <AvatarFallback className="bg-primary text-primary-foreground">
                    {user?.full_name?.charAt(0).toUpperCase() || 'U'}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 text-left">
                  <p className="text-sm font-medium leading-none">{user?.full_name}</p>
                  <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                </div>
                <ChevronLeft className="h-4 w-4 text-muted-foreground rotate-180" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-56">
              <DropdownMenuLabel>Tài khoản</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => navigate('/profile')}>
                <User className="mr-2 h-4 w-4" /> Hồ sơ
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate('/settings')}>
                <Settings className="mr-2 h-4 w-4" /> Cài đặt
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => { logout(); navigate('/login'); }}>
                <LogOut className="mr-2 h-4 w-4" /> Đăng xuất
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex-1 flex flex-col">
        {/* Top navbar */}
        <header className="flex h-16 items-center gap-4 border-b bg-card px-4 lg:px-6">
          <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="lg:hidden">
                <Menu className="h-5 w-5" />
                <span className="sr-only">Mở menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-64 p-0">
              <div className="flex items-center h-16 px-4 border-b bg-card">
                <span className="font-semibold text-lg">AI Văn bản</span>
              </div>
              <div className="py-4">
                <NavItems />
              </div>
            </SheetContent>
          </Sheet>
          <div className="flex-1" />
          <div className="flex items-center gap-2">
            <NotificationBell />
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-6 bg-muted/30">
          <Outlet />
        </main>
      </div>
    </div>
  );
}