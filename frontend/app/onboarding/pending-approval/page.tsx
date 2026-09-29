'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/lib/store/auth-store';
import { AuthGuard } from '@/components/auth/auth-guard';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Building2, Clock, RefreshCw, LogOut, CheckCircle2, XCircle } from 'lucide-react';

function PendingApprovalContent() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const setMembership = useAuthStore((state) => state.setMembership);

  const [checking, setChecking] = useState(false);
  const [membershipStatus, setMembershipStatus] = useState<string>(user?.membership_status || 'pending');

  const checkStatus = useCallback(async () => {
    setChecking(true);
    try {
      const response = await apiClient.get('/societies/membership/status');
      const list = response.data?.data || [];
      if (Array.isArray(list) && list.length > 0) {
        const latest = list[0];
        setMembershipStatus(latest.status);

        if (latest.status === 'approved') {
          setMembership(latest.society_id, latest.role || 'resident', 'approved');
          router.replace('/resident/dashboard');
        } else if (latest.status === 'rejected') {
          setMembership(null, 'resident', 'unlinked');
        }
      }
    } catch {
      // Gracefully silent in polling; user can retry with manual button
    } finally {
      setChecking(false);
    }
  }, [router, setMembership]);

  // Periodic polling every 20 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      checkStatus();
    }, 20000);

    return () => clearInterval(timer);
  }, [checkStatus]);

  return (
    <div className="min-h-screen flex flex-col bg-zinc-50 dark:bg-black font-sans">
      {/* Top Bar */}
      <header className="border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 px-6 py-4 flex justify-between items-center">
        <Link href="/" className="flex items-center gap-2 font-bold text-lg text-zinc-900 dark:text-zinc-50">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-900 text-white dark:bg-zinc-50 dark:text-zinc-900">
            <Building2 className="h-5 w-5" />
          </div>
          <span>SocietySync</span>
        </Link>

        <div className="flex items-center gap-4 text-sm">
          <span className="text-zinc-600 dark:text-zinc-400">
            Signed in as <strong className="text-zinc-900 dark:text-zinc-100">{user?.first_name} {user?.last_name}</strong>
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              logout();
              router.replace('/login');
            }}
            className="flex items-center gap-1.5"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span>Sign Out</span>
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex justify-center items-center px-4 py-12">
        <div className="w-full max-w-md">
          <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 shadow-sm text-center">
            {membershipStatus === 'approved' ? (
              <CardContent className="pt-10 pb-10 space-y-4">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400">
                  <CheckCircle2 className="h-8 w-8" />
                </div>
                <CardTitle className="text-2xl font-bold">Membership Approved!</CardTitle>
                <CardDescription className="text-sm text-zinc-600 dark:text-zinc-400">
                  Your request has been approved. Redirecting to your resident dashboard...
                </CardDescription>
              </CardContent>
            ) : membershipStatus === 'rejected' ? (
              <CardContent className="pt-10 pb-10 space-y-4">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-red-50 dark:bg-red-950/50 text-red-600 dark:text-red-400">
                  <XCircle className="h-8 w-8" />
                </div>
                <CardTitle className="text-2xl font-bold">Request Not Approved</CardTitle>
                <CardDescription className="text-sm text-zinc-600 dark:text-zinc-400 max-w-xs mx-auto">
                  The society administrator was unable to verify your flat details. Please try requesting membership again or contact your society committee.
                </CardDescription>
                <div className="pt-4">
                  <Button onClick={() => router.replace('/onboarding/join-society')} className="w-full h-10">
                    Find Another Society
                  </Button>
                </div>
              </CardContent>
            ) : (
              /* Pending Status */
              <>
                <CardHeader className="pb-2">
                  <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400">
                    <Clock className="h-7 w-7 animate-pulse" />
                  </div>
                  <CardTitle className="text-2xl font-bold">Membership Pending</CardTitle>
                  <CardDescription className="text-sm text-zinc-600 dark:text-zinc-400 max-w-sm mx-auto">
                    Your request has been submitted to the Society Management Committee for verification.
                  </CardDescription>
                </CardHeader>

                <CardContent className="space-y-4 pt-2 pb-6">
                  <div className="p-3.5 rounded-lg bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed text-left">
                    💡 Once approved by your society admin, you will automatically gain access to maintenance bill payments, gate visitor passes, notice board circulars, and complaint tickets.
                  </div>

                  <Button
                    onClick={checkStatus}
                    disabled={checking}
                    variant="outline"
                    className="w-full h-10 flex items-center justify-center gap-2"
                  >
                    <RefreshCw className={`h-4 w-4 ${checking ? 'animate-spin' : ''}`} />
                    <span>{checking ? 'Checking Status...' : 'Check Approval Status'}</span>
                  </Button>
                </CardContent>
              </>
            )}
          </Card>
        </div>
      </main>
    </div>
  );
}

export default function PendingApprovalPage() {
  return (
    <AuthGuard>
      <PendingApprovalContent />
    </AuthGuard>
  );
}
