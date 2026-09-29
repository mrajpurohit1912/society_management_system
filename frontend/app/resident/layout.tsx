'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { AuthGuard } from '@/components/auth/auth-guard';
import { useAuthStore } from '@/lib/store/auth-store';
import { Button } from '@/components/ui/button';
import {
  Home,
  LayoutDashboard,
  ShieldCheck,
  Bell,
  Wrench,
  CreditCard,
  LogOut,
  Menu,
  X,
  QrCode,
} from 'lucide-react';

const residentNavItems = [
  { name: 'Home & Flat', href: '/resident/dashboard', icon: LayoutDashboard },
  { name: 'Visitor Gate Passes', href: '/resident/visitors', icon: QrCode },
  { name: 'Maintenance & Dues', href: '/resident/payments', icon: CreditCard },
  { name: 'Society Notices', href: '/resident/notices', icon: Bell },
  { name: 'Helpdesk Tickets', href: '/resident/complaints', icon: Wrench },
];

function ResidentLayoutContent({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleSignOut = () => {
    logout();
    router.replace('/login');
  };

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-black font-sans flex">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex w-64 flex-col border-r border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
        {/* Brand */}
        <div className="h-16 px-6 flex items-center gap-2 border-b border-zinc-200 dark:border-zinc-800">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-white">
            <Home className="h-5 w-5" />
          </div>
          <div>
            <span className="font-bold text-base block text-zinc-900 dark:text-zinc-100 leading-tight">
              SocietySync
            </span>
            <span className="text-[10px] text-zinc-500 uppercase tracking-wider font-semibold">
              Resident App
            </span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {residentNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-indigo-600 text-white'
                    : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-900 hover:text-zinc-900 dark:hover:text-zinc-100'
                }`}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* User Card & Logout */}
        <div className="p-4 border-t border-zinc-200 dark:border-zinc-800 space-y-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-semibold text-xs">
              {user?.first_name?.[0] || 'R'}
              {user?.last_name?.[0] || ''}
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-semibold text-zinc-900 dark:text-zinc-100 truncate">
                {user?.first_name} {user?.last_name}
              </p>
              <div className="flex items-center gap-1 text-[11px] text-indigo-600 dark:text-indigo-400 font-medium">
                <ShieldCheck className="h-3 w-3" />
                <span>Verified Resident</span>
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

      {/* Main View Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 px-4 md:px-8 flex justify-between items-center md:hidden">
          <Link href="/resident/dashboard" className="flex items-center gap-2 font-bold text-base">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white">
              <Home className="h-4 w-4" />
            </div>
            <span>SocietySync Resident</span>
          </Link>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-lg text-zinc-600 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-900"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </header>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 px-4 py-3 space-y-1">
            {residentNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-zinc-600 dark:text-zinc-400'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
            <div className="pt-2">
              <Button variant="outline" size="sm" onClick={handleSignOut} className="w-full h-8 text-xs">
                Sign Out
              </Button>
            </div>
          </div>
        )}

        <main className="flex-1 overflow-y-auto p-4 md:p-8">{children}</main>
      </div>
    </div>
  );
}

export default function ResidentLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard allowedRoles={['resident', 'society_admin', 'platform_admin']}>
      <ResidentLayoutContent>{children}</ResidentLayoutContent>
    </AuthGuard>
  );
}
