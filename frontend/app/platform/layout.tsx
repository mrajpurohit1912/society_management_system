'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { AuthGuard } from '@/components/auth/auth-guard';
import { useAuthStore } from '@/lib/store/auth-store';
import { Button } from '@/components/ui/button';
import {
  ShieldCheck,
  LayoutDashboard,
  LogOut,
  Building2,
} from 'lucide-react';

function PlatformLayoutContent({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  const handleSignOut = () => {
    logout();
    router.replace('/login');
  };

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-black font-sans flex">
      {/* Sidebar */}
      <aside className="w-64 flex-col border-r border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 hidden md:flex">
        {/* Brand */}
        <div className="h-16 px-6 flex items-center gap-2 border-b border-zinc-200 dark:border-zinc-800">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-purple-600 text-white">
            <Building2 className="h-5 w-5" />
          </div>
          <div>
            <span className="font-bold text-base block text-zinc-900 dark:text-zinc-100 leading-tight">
              SocietySync
            </span>
            <span className="text-[10px] text-purple-600 dark:text-purple-400 uppercase tracking-wider font-bold">
              Platform Super-Admin
            </span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          <Link
            href="/platform/dashboard"
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
              pathname === '/platform/dashboard'
                ? 'bg-purple-600 text-white'
                : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-900'
            }`}
          >
            <LayoutDashboard className="h-4 w-4 shrink-0" />
            <span>Leads & Provisioning</span>
          </Link>
        </nav>

        {/* User Card */}
        <div className="p-4 border-t border-zinc-200 dark:border-zinc-800 space-y-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 font-semibold text-xs">
              SA
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-semibold text-zinc-900 dark:text-zinc-100 truncate">
                {user?.first_name} {user?.last_name}
              </p>
              <div className="flex items-center gap-1 text-[11px] text-purple-600 font-medium">
                <ShieldCheck className="h-3 w-3" />
                <span>Super Administrator</span>
              </div>
            </div>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={handleSignOut}
            className="w-full h-8 text-xs flex items-center justify-center gap-1.5"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span>Sign Out</span>
          </Button>
        </div>
      </aside>

      {/* Main Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 px-4 md:px-8 flex justify-between items-center md:hidden">
          <div className="flex items-center gap-2 font-bold text-base">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-600 text-white">
              <Building2 className="h-4 w-4" />
            </div>
            <span>Platform Super-Admin</span>
          </div>
          <Button variant="outline" size="sm" onClick={handleSignOut} className="h-8 text-xs">
            Sign Out
          </Button>
        </header>

        <main className="flex-1 overflow-y-auto p-4 md:p-8">{children}</main>
      </div>
    </div>
  );
}

export default function PlatformLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard allowedRoles={['platform_admin']}>
      <PlatformLayoutContent>{children}</PlatformLayoutContent>
    </AuthGuard>
  );
}
