'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/lib/store/auth-store';
import { buttonVariants } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import {
  Building2,
  Users,
  Bell,
  Wrench,
  CreditCard,
  ArrowRight,
  Loader2,
  ShieldCheck,
  PlusCircle,
  MapPin,
  Mail,
  Phone,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface SocietyDetail {
  id: string;
  name: string;
  city: string;
  state: string;
  registration_no?: string;
  address?: string;
  country?: string;
  zipcode?: string;
  email?: string;
  phone?: string;
  status?: string;
}

export default function AdminDashboardPage() {
  const user = useAuthStore((state) => state.user);
  const societyId = user?.active_society_id;

  const [society, setSociety] = useState<SocietyDetail | null>(null);
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [noticeCount, setNoticeCount] = useState<number>(0);
  const [complaintCount, setComplaintCount] = useState<number>(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!societyId) {
      setLoading(false);
      return;
    }

    let isMounted = true;

    const fetchDashboardData = async () => {
      try {
        // Fetch society details, pending requests, notices in parallel
        const [socRes, reqRes, noticeRes, compRes] = await Promise.allSettled([
          apiClient.get(`/societies/${societyId}`),
          apiClient.get(`/societies/${societyId}/membership/requests`),
          apiClient.get(`/societies/${societyId}/notices`),
          apiClient.get(`/societies/${societyId}/complaints`),
        ]);

        if (isMounted) {
          if (socRes.status === 'fulfilled') {
            setSociety(socRes.value.data?.data || socRes.value.data || null);
          }
          if (reqRes.status === 'fulfilled') {
            const list = reqRes.value.data?.data || reqRes.value.data || [];
            setPendingCount(Array.isArray(list) ? list.length : 0);
          }
          if (noticeRes.status === 'fulfilled') {
            const list = noticeRes.value.data?.data || noticeRes.value.data || [];
            setNoticeCount(Array.isArray(list) ? list.length : 0);
          }
          if (compRes.status === 'fulfilled') {
            const list = compRes.value.data?.data || compRes.value.data || [];
            const openList = Array.isArray(list)
              ? list.filter((c: { status?: string }) => c.status !== 'resolved' && c.status !== 'closed')
              : [];
            setComplaintCount(openList.length);
          }
        }
      } catch {
        // Fallbacks preserved
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchDashboardData();

    return () => {
      isMounted = false;
    };
  }, [societyId]);

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-200 dark:border-zinc-800 pb-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
            {society?.name || 'Society Admin Console'}
          </h1>
          <p className="text-sm text-zinc-500 mt-1 flex items-center gap-1.5">
            <ShieldCheck className="h-4 w-4 text-emerald-600" />
            <span>
              {society?.city ? `${society.city}, ${society.state}` : 'Residential Management Portal'}
            </span>
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link
            href="/admin/notices"
            className={buttonVariants({ size: 'sm', className: 'flex items-center gap-1.5' })}
          >
            <PlusCircle className="h-4 w-4" />
            <span>Post Notice</span>
          </Link>
          <Link
            href="/admin/residents"
            className={buttonVariants({ variant: 'outline', size: 'sm', className: 'flex items-center gap-1.5' })}
          >
            <Users className="h-4 w-4" />
            <span>Approvals ({pendingCount})</span>
          </Link>
        </div>
      </div>

      {/* Society Details & Information Overview Card */}
      <Card className="border border-zinc-200 dark:border-zinc-800 bg-gradient-to-br from-indigo-50/40 via-white to-zinc-50/50 dark:from-zinc-950 dark:via-zinc-900/40 dark:to-zinc-950 shadow-sm overflow-hidden">
        <div className="p-5 flex flex-col lg:flex-row lg:items-center justify-between gap-5">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-600 text-white font-bold text-lg shadow-sm shrink-0">
              <Building2 className="h-6 w-6" />
            </div>
            <div className="space-y-1.5">
              <div className="flex items-center gap-2.5 flex-wrap">
                <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-50">
                  {society?.name || 'Society Admin Console'}
                </h2>
                {society?.registration_no && (
                  <Badge variant="outline" className="font-mono text-[11px] border-indigo-200 dark:border-indigo-800 text-indigo-700 dark:text-indigo-300">
                    REG: {society.registration_no}
                  </Badge>
                )}
                <Badge className="bg-emerald-600 text-white text-[10px]">
                  {society?.status ? society.status.toUpperCase() : 'ACTIVE'}
                </Badge>
              </div>

              <div className="flex items-center gap-4 text-xs text-zinc-500 flex-wrap pt-0.5">
                {society?.address && (
                  <span className="flex items-center gap-1 text-zinc-700 dark:text-zinc-300">
                    <MapPin className="h-3.5 w-3.5 text-zinc-400 shrink-0" />
                    <span>
                      {society.address}, {society.city}, {society.state} {society.zipcode ? `- ${society.zipcode}` : ''}
                    </span>
                  </span>
                )}
                {society?.email && (
                  <a
                    href={`mailto:${society.email}`}
                    className="flex items-center gap-1 hover:text-indigo-600 text-zinc-600 dark:text-zinc-400"
                  >
                    <Mail className="h-3.5 w-3.5 text-zinc-400 shrink-0" />
                    <span>{society.email}</span>
                  </a>
                )}
                {society?.phone && (
                  <a
                    href={`tel:${society.phone}`}
                    className="flex items-center gap-1 hover:text-indigo-600 text-zinc-600 dark:text-zinc-400"
                  >
                    <Phone className="h-3.5 w-3.5 text-zinc-400 shrink-0" />
                    <span>{society.phone}</span>
                  </a>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 border-t lg:border-t-0 pt-3 lg:pt-0 lg:pl-4 border-zinc-200 dark:border-zinc-800 shrink-0">
            <Link
              href="/admin/units"
              className={buttonVariants({
                variant: 'outline',
                size: 'sm',
                className: 'h-8 text-xs flex items-center gap-1.5',
              })}
            >
              <Building2 className="h-3.5 w-3.5 text-indigo-600" />
              <span>Buildings & Units</span>
            </Link>
            <Link
              href="/admin/residents"
              className={buttonVariants({
                variant: 'outline',
                size: 'sm',
                className: 'h-8 text-xs flex items-center gap-1.5',
              })}
            >
              <Users className="h-3.5 w-3.5 text-indigo-600" />
              <span>Residents Directory</span>
            </Link>
          </div>
        </div>
      </Card>

      {/* KPI Cards */}
      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Pending Approvals */}
          <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                Pending Approvals
              </CardTitle>
              <Users className="h-4 w-4 text-amber-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">{pendingCount}</div>
              <p className="text-xs text-zinc-500 mt-1">Residents waiting for verification</p>
              <Link
                href="/admin/residents"
                className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-zinc-900 dark:text-zinc-100 hover:underline"
              >
                <span>Review requests</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
            </CardContent>
          </Card>

          {/* Card 2: Active Notices */}
          <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                Published Notices
              </CardTitle>
              <Bell className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">{noticeCount}</div>
              <p className="text-xs text-zinc-500 mt-1">Active broadcast circulars</p>
              <Link
                href="/admin/notices"
                className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-zinc-900 dark:text-zinc-100 hover:underline"
              >
                <span>Manage notices</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
            </CardContent>
          </Card>

          {/* Card 3: Open Complaints */}
          <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                Open Complaints
              </CardTitle>
              <Wrench className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">{complaintCount}</div>
              <p className="text-xs text-zinc-500 mt-1">Unresolved resident tickets</p>
              <Link
                href="/admin/complaints"
                className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-zinc-900 dark:text-zinc-100 hover:underline"
              >
                <span>Helpdesk tickets</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
            </CardContent>
          </Card>

          {/* Card 4: Billing Quick Access */}
          <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                Maintenance Billing
              </CardTitle>
              <CreditCard className="h-4 w-4 text-emerald-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">Active</div>
              <p className="text-xs text-zinc-500 mt-1">Invoices & monthly dues</p>
              <Link
                href="/admin/maintenance"
                className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-zinc-900 dark:text-zinc-100 hover:underline"
              >
                <span>Billing console</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Quick Action Hub */}
      <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
        <CardHeader>
          <CardTitle className="text-lg font-bold">Quick Administrative Workflows</CardTitle>
          <CardDescription>Common operations for managing your society operations</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 space-y-2">
            <div className="h-8 w-8 rounded-lg bg-amber-50 dark:bg-amber-950/50 flex items-center justify-center text-amber-600 dark:text-amber-400">
              <Users className="h-4 w-4" />
            </div>
            <h3 className="font-semibold text-sm">Resident Membership Desk</h3>
            <p className="text-xs text-zinc-500">Verify and link new homeowners and tenants to flats.</p>
            <Link
              href="/admin/residents"
              className={buttonVariants({ variant: 'outline', size: 'sm', className: 'w-full mt-2 justify-center' })}
            >
              Go to Approvals
            </Link>
          </div>

          <div className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 space-y-2">
            <div className="h-8 w-8 rounded-lg bg-blue-50 dark:bg-blue-950/50 flex items-center justify-center text-blue-600 dark:text-blue-400">
              <Bell className="h-4 w-4" />
            </div>
            <h3 className="font-semibold text-sm">Publish Circulars</h3>
            <p className="text-xs text-zinc-500">Post announcements and event circulars to residents.</p>
            <Link
              href="/admin/notices"
              className={buttonVariants({ variant: 'outline', size: 'sm', className: 'w-full mt-2 justify-center' })}
            >
              Manage Circulars
            </Link>
          </div>

          <div className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 space-y-2">
            <div className="h-8 w-8 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
              <Building2 className="h-4 w-4" />
            </div>
            <h3 className="font-semibold text-sm">Flats & Towers Directory</h3>
            <p className="text-xs text-zinc-500">Configure building wings, floors, and flat units.</p>
            <Link
              href="/admin/units"
              className={buttonVariants({ variant: 'outline', size: 'sm', className: 'w-full mt-2 justify-center' })}
            >
              Configure Flats
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
