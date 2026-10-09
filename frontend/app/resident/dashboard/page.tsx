'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/lib/store/auth-store';
import { buttonVariants } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  QrCode,
  CreditCard,
  Wrench,
  Bell,
  ArrowRight,
  Loader2,
  ShieldCheck,
  PlusCircle,
  Calendar,
  Eye,
} from 'lucide-react';

interface Notice {
  id: string;
  title: string;
  category: string;
  priority: string;
  is_pinned: boolean;
  published_at: string;
}

interface VisitorPass {
  id: string;
  visitor_name: string;
  passcode: string;
  visitor_type: string;
  status: string;
  valid_until: string;
}

export default function ResidentDashboardPage() {
  const user = useAuthStore((state) => state.user);
  const societyId = user?.active_society_id;

  const [notices, setNotices] = useState<Notice[]>([]);
  const [visitorPasses, setVisitorPasses] = useState<VisitorPass[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!societyId) {
      setLoading(false);
      return;
    }

    let isMounted = true;
    const fetchDashboard = async () => {
      try {
        const [noticesRes, passesRes] = await Promise.allSettled([
          apiClient.get(`/societies/${societyId}/notices`),
          apiClient.get(`/societies/${societyId}/visitor-passes`),
        ]);

        if (isMounted) {
          if (noticesRes.status === 'fulfilled') {
            const list = noticesRes.value.data?.data || noticesRes.value.data || [];
            setNotices(Array.isArray(list) ? list.slice(0, 3) : []);
          }
          if (passesRes.status === 'fulfilled') {
            const list = passesRes.value.data?.data || passesRes.value.data || [];
            setVisitorPasses(Array.isArray(list) ? list.slice(0, 3) : []);
          }
        }
      } catch {
        // Fallbacks preserved
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchDashboard();

    return () => {
      isMounted = false;
    };
  }, [societyId]);

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-200 dark:border-zinc-800 pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
            Welcome home, {user?.first_name || 'Resident'}!
          </h1>
          <p className="text-sm text-zinc-500 mt-1 flex items-center gap-1.5">
            <ShieldCheck className="h-4 w-4 text-indigo-600" />
            <span>Residential Dashboard • Gated Community Member</span>
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/resident/visitors"
            className={buttonVariants({
              size: 'sm',
              className: 'bg-indigo-600 hover:bg-indigo-700 text-white flex items-center gap-1.5 font-semibold',
            })}
          >
            <PlusCircle className="h-4 w-4" />
            <span>New Visitor Pass</span>
          </Link>
          <Link
            href="/resident/complaints"
            className={buttonVariants({
              variant: 'outline',
              size: 'sm',
              className: 'flex items-center gap-1.5',
            })}
          >
            <Wrench className="h-4 w-4" />
            <span>Raise Ticket</span>
          </Link>
        </div>
      </div>

      {/* Quick Action Tiles */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Pass Shortcut */}
        <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 hover:border-indigo-300 dark:hover:border-indigo-800 transition-all">
          <CardHeader className="pb-2 flex flex-row items-center justify-between">
            <CardTitle className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
              Gate Entry Pass
            </CardTitle>
            <QrCode className="h-4 w-4 text-indigo-600" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold text-zinc-900 dark:text-zinc-100">Quick Gate Pass</div>
            <p className="text-xs text-zinc-500 mt-1">
              Pre-approve guests, delivery agents & cabs with a 6-digit OTP.
            </p>
            <Link
              href="/resident/visitors"
              className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              <span>Generate pass</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </CardContent>
        </Card>

        {/* Maintenance Dues Shortcut */}
        <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 hover:border-emerald-300 dark:hover:border-emerald-800 transition-all">
          <CardHeader className="pb-2 flex flex-row items-center justify-between">
            <CardTitle className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
              Maintenance Dues
            </CardTitle>
            <CreditCard className="h-4 w-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold text-zinc-900 dark:text-zinc-100">Pay Dues</div>
            <p className="text-xs text-zinc-500 mt-1">
              View monthly society invoices and pay securely online or submit UTR.
            </p>
            <Link
              href="/resident/payments"
              className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-emerald-600 dark:text-emerald-400 hover:underline"
            >
              <span>View invoices</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </CardContent>
        </Card>

        {/* Helpdesk Shortcut */}
        <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 hover:border-amber-300 dark:hover:border-amber-800 transition-all">
          <CardHeader className="pb-2 flex flex-row items-center justify-between">
            <CardTitle className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
              Service Helpdesk
            </CardTitle>
            <Wrench className="h-4 w-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold text-zinc-900 dark:text-zinc-100">Report Issue</div>
            <p className="text-xs text-zinc-500 mt-1">
              Plumbing, electrical, or elevator maintenance with guaranteed SLA.
            </p>
            <Link
              href="/resident/complaints"
              className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-amber-600 dark:text-amber-400 hover:underline"
            >
              <span>Open ticket</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Main Grid: Latest Notices & Recent Visitor Passes */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Latest Notices */}
        <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-base font-semibold flex items-center gap-2">
                <Bell className="h-4 w-4 text-zinc-500" />
                <span>Notice Board</span>
              </CardTitle>
              <CardDescription className="text-xs">Latest society broadcasts and announcements</CardDescription>
            </div>
            <Link
              href="/resident/notices"
              className="text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:underline"
            >
              View all
            </Link>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
              </div>
            ) : notices.length === 0 ? (
              <p className="text-xs text-zinc-500 italic py-6 text-center">
                No active announcements right now.
              </p>
            ) : (
              <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {notices.map((n) => (
                  <div key={n.id} className="py-3 space-y-1">
                    <div className="flex items-center justify-between">
                      <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 truncate">
                        {n.title}
                      </h2>
                      <div className="flex items-center gap-1.5">
                        <Badge variant="outline" className="text-[10px] capitalize">
                          {n.category.replace(/_/g, ' ')}
                        </Badge>
                        <Link
                          href="/resident/notices"
                          className={buttonVariants({
                            variant: 'ghost',
                            size: 'sm',
                            className: 'h-6 px-1.5 text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 flex items-center gap-1',
                          })}
                        >
                          <Eye className="h-3 w-3" />
                          <span>View</span>
                        </Link>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-[11px] text-zinc-400">
                      <Calendar className="h-3 w-3" />
                      <span>{new Date(n.published_at).toLocaleDateString()}</span>
                      {n.is_pinned && <span className="text-amber-600 font-bold">• Pinned</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Visitor Passes */}
        <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-base font-semibold flex items-center gap-2">
                <QrCode className="h-4 w-4 text-zinc-500" />
                <span>Recent Passes</span>
              </CardTitle>
              <CardDescription className="text-xs">Active entry codes for security gate</CardDescription>
            </div>
            <Link
              href="/resident/visitors"
              className="text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:underline"
            >
              Manage
            </Link>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
              </div>
            ) : visitorPasses.length === 0 ? (
              <p className="text-xs text-zinc-500 italic py-6 text-center">
                No active passes. Generate one when a guest is arriving.
              </p>
            ) : (
              <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {visitorPasses.map((p) => (
                  <div key={p.id} className="py-3 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                        {p.visitor_name}
                      </p>
                      <p className="text-[11px] text-zinc-400 capitalize">
                        {p.visitor_type} • Valid until {new Date(p.valid_until).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-sm bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 px-2 py-1 rounded">
                        {p.passcode}
                      </span>
                      <Link
                        href="/resident/visitors"
                        className={buttonVariants({
                          variant: 'ghost',
                          size: 'sm',
                          className: 'h-6 px-1.5 text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 flex items-center gap-1',
                        })}
                      >
                        <Eye className="h-3 w-3" />
                        <span>View</span>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
