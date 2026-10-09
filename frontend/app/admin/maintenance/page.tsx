'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/lib/store/auth-store';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  CreditCard,
  CheckCircle,
  XCircle,
  Loader2,
  AlertCircle,
  FileText,
  DollarSign,
  Clock,
  Send,
  Building,
  Eye,
  User,
  Home,
  Phone,
  Mail,
  Search,
  ChevronRight,
  BarChart3,
  RefreshCw,
} from 'lucide-react';

interface CollectionSummary {
  total_invoiced: number;
  total_collected: number;
  total_pending: number;
  pending_approval_count: number;
}

interface Invoice {
  id: string;
  society_id: string;
  unit_id: string;
  billing_period: string;
  title: string;
  description?: string;
  amount: number;
  due_date: string;
  penalty_amount: number;
  status: string;
  created_at: string;
  unit_number?: string;
  building_name?: string;
  floor_number?: number;
  resident_name?: string;
  resident_email?: string;
  resident_phone?: string;
  residency_type?: string;
}

interface OfflinePayment {
  id: string;
  society_id: string;
  invoice_id?: string;
  unit_id?: string;
  user_id: string;
  amount: number;
  payment_method: string;
  status: string;
  transaction_reference?: string;
  description?: string;
  created_at: string;
  user_name?: string;
  user_email?: string;
  user_phone?: string;
  unit_number?: string;
  building_name?: string;
  invoice_title?: string;
}

const formatDate = (dateStr: string) => {
  try {
    const d = new Date(dateStr);
    return isNaN(d.getTime()) ? dateStr : d.toLocaleDateString(undefined, { dateStyle: 'medium' });
  } catch {
    return dateStr;
  }
};

const formatDateTime = (dateStr: string) => {
  try {
    const d = new Date(dateStr);
    return isNaN(d.getTime())
      ? dateStr
      : `${d.toLocaleDateString(undefined, { dateStyle: 'medium' })}, ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
  } catch {
    return dateStr;
  }
};

export default function AdminMaintenancePage() {
  const user = useAuthStore((state) => state.user);
  const societyId = user?.active_society_id;

  const [activeTab, setActiveTab] = useState<'invoices' | 'generate' | 'approvals'>('invoices');
  const [summary, setSummary] = useState<CollectionSummary | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [pendingPayments, setPendingPayments] = useState<OfflinePayment[]>([]);
  const [viewingInvoice, setViewingInvoice] = useState<Invoice | null>(null);
  const [viewingPayment, setViewingPayment] = useState<OfflinePayment | null>(null);

  // Search & Filter state for Invoices Directory
  const [invoiceStatusFilter, setInvoiceStatusFilter] = useState<'all' | 'pending' | 'paid' | 'overdue'>('all');
  const [invoiceSearchQuery, setInvoiceSearchQuery] = useState('');
  const [showFinancialReport, setShowFinancialReport] = useState(false);

  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Bulk Generator Form State
  const [bulkPeriod, setBulkPeriod] = useState('2026-10');
  const [bulkTitle, setBulkTitle] = useState('Monthly Maintenance - Oct 2026');
  const [bulkAmount, setBulkAmount] = useState(3500);
  const [bulkDueDays, setBulkDueDays] = useState(15);
  const [bulkDesc, setBulkDesc] = useState('Society maintenance dues covering security, electricity, water, and elevator upkeep.');

  // Fetch summary and data
  const fetchData = useCallback(async () => {
    if (!societyId) {
      setLoading(false);
      return;
    }

    try {
      const [sumRes, invRes, pendRes] = await Promise.allSettled([
        apiClient.get(`/societies/${societyId}/collection-summary`),
        apiClient.get(`/societies/${societyId}/invoices`),
        apiClient.get(`/societies/${societyId}/payments/pending-approval`),
      ]);

      if (sumRes.status === 'fulfilled') {
        setSummary(sumRes.value.data?.data || sumRes.value.data || null);
      }
      if (invRes.status === 'fulfilled') {
        const list = invRes.value.data?.data || invRes.value.data || [];
        setInvoices(Array.isArray(list) ? list : []);
      }
      if (pendRes.status === 'fulfilled') {
        const list = pendRes.value.data?.data || pendRes.value.data || [];
        setPendingPayments(Array.isArray(list) ? list : []);
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      }
    } finally {
      setLoading(false);
    }
  }, [societyId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Bulk Invoice Generation Submit
  const handleBulkGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!societyId) return;

    setActionLoading('bulk-generate');
    setFeedback(null);

    try {
      const res = await apiClient.post(`/societies/${societyId}/invoices/bulk-generate`, {
        billing_period: bulkPeriod.trim(),
        title: bulkTitle.trim(),
        amount: Number(bulkAmount),
        due_date_days: Number(bulkDueDays),
        description: bulkDesc.trim(),
      });
      const generatedList = res.data?.data || res.data || [];
      const count = Array.isArray(generatedList) ? generatedList.length : 0;
      setFeedback({
        type: 'success',
        message: `Successfully generated ${count} maintenance invoices for billing period ${bulkPeriod}!`,
      });
      setActiveTab('invoices');
      await fetchData();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to generate monthly invoices.' });
      }
    } finally {
      setActionLoading(null);
    }
  };

  // Review Offline Payment (Approve / Reject)
  const handleReviewPayment = async (paymentId: string, approved: boolean) => {
    if (!societyId) return;

    setActionLoading(paymentId);
    setFeedback(null);

    try {
      await apiClient.post(`/societies/${societyId}/payments/${paymentId}/review`, {
        approved,
        rejection_reason: approved ? undefined : 'Transaction reference / UTR could not be verified in bank statement.',
      });

      setFeedback({
        type: 'success',
        message: approved
          ? 'Payment approved! Invoice marked as PAID and official receipt issued.'
          : 'Payment rejected. Resident notified.',
      });
      setPendingPayments((prev) => prev.filter((p) => p.id !== paymentId));
      await fetchData();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to process payment review.' });
      }
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'paid':
        return <Badge className="bg-emerald-600 text-white text-[10px]">PAID</Badge>;
      case 'overdue':
        return <Badge variant="destructive" className="text-[10px]">OVERDUE</Badge>;
      case 'pending':
        return <Badge variant="outline" className="border-amber-500 text-amber-600 dark:text-amber-400 text-[10px] font-semibold">PENDING</Badge>;
      case 'partially_paid':
        return <Badge variant="secondary" className="text-[10px]">PARTIALLY PAID</Badge>;
      default:
        return <Badge variant="outline" className="text-[10px]">{status}</Badge>;
    }
  };

  // Counts and filtered lists
  const paidInvoices = invoices.filter((i) => i.status.toLowerCase() === 'paid');
  const pendingInvoices = invoices.filter((i) => i.status.toLowerCase() === 'pending');
  const overdueInvoices = invoices.filter((i) => i.status.toLowerCase() === 'overdue');

  const filteredInvoices = invoices.filter((inv) => {
    // Status filter
    if (invoiceStatusFilter !== 'all' && inv.status.toLowerCase() !== invoiceStatusFilter) {
      return false;
    }
    // Search query
    if (invoiceSearchQuery.trim()) {
      const q = invoiceSearchQuery.toLowerCase();
      const matchUnit = inv.unit_number?.toLowerCase().includes(q);
      const matchWing = inv.building_name?.toLowerCase().includes(q);
      const matchResident = inv.resident_name?.toLowerCase().includes(q);
      const matchPhone = inv.resident_phone?.toLowerCase().includes(q);
      const matchEmail = inv.resident_email?.toLowerCase().includes(q);
      const matchTitle = inv.title.toLowerCase().includes(q);
      const matchPeriod = inv.billing_period.toLowerCase().includes(q);
      return Boolean(matchUnit || matchWing || matchResident || matchPhone || matchEmail || matchTitle || matchPeriod);
    }
    return true;
  });

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-200 dark:border-zinc-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 flex items-center gap-2">
            <CreditCard className="h-6 w-6" />
            <span>Maintenance Invoicing & Billing</span>
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            Generate monthly dues, track collections, inspect flat owners, and verify resident bank transfers.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowFinancialReport(true)}
            className="h-8 text-xs font-semibold flex items-center gap-1.5 border-zinc-200 dark:border-zinc-800"
          >
            <BarChart3 className="h-3.5 w-3.5 text-indigo-600" />
            <span>Financial Breakdown</span>
          </Button>
          <Button
            size="sm"
            onClick={() => setActiveTab('generate')}
            className="bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 h-8 text-xs font-semibold flex items-center gap-1.5"
          >
            <Send className="h-3.5 w-3.5" />
            <span>Generate Invoices</span>
          </Button>
        </div>
      </div>

      {/* Feedback Banner */}
      {feedback && (
        <div
          className={`p-3.5 rounded-lg text-sm flex items-center gap-2 border ${
            feedback.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800 dark:bg-emerald-950/50 dark:border-emerald-900 dark:text-emerald-300'
              : 'bg-red-50 border-red-200 text-red-800 dark:bg-red-950/50 dark:border-red-900 dark:text-red-300'
          }`}
        >
          {feedback.type === 'success' ? (
            <CheckCircle className="h-4 w-4 shrink-0 text-emerald-600" />
          ) : (
            <AlertCircle className="h-4 w-4 shrink-0 text-red-600" />
          )}
          <span>{feedback.message}</span>
        </div>
      )}

      {/* Financial KPIs - Interactive Cards with Drilldown Views */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Invoiced */}
        <Card
          onClick={() => {
            setActiveTab('invoices');
            setInvoiceStatusFilter('all');
          }}
          className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 hover:border-blue-500/50 dark:hover:border-blue-500/50 transition cursor-pointer group shadow-sm hover:shadow"
        >
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
              Total Invoiced
            </CardTitle>
            <div className="p-1.5 rounded-md bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400">
              <DollarSign className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">
              ₹{(summary?.total_invoiced || 0).toLocaleString()}
            </div>
            <p className="text-xs text-zinc-500 mt-1">Total dues issued to residents</p>
            <div className="mt-3 pt-2.5 border-t border-zinc-100 dark:border-zinc-800/80 flex items-center justify-between text-xs text-blue-600 dark:text-blue-400 font-medium group-hover:underline">
              <span>View Directory ({invoices.length})</span>
              <ChevronRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition-transform" />
            </div>
          </CardContent>
        </Card>

        {/* Total Collected */}
        <Card
          onClick={() => {
            setActiveTab('invoices');
            setInvoiceStatusFilter('paid');
          }}
          className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 hover:border-emerald-500/50 dark:hover:border-emerald-500/50 transition cursor-pointer group shadow-sm hover:shadow"
        >
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
              Total Collected
            </CardTitle>
            <div className="p-1.5 rounded-md bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400">
              <CheckCircle className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
              ₹{(summary?.total_collected || 0).toLocaleString()}
            </div>
            <p className="text-xs text-zinc-500 mt-1">Settled payments in account</p>
            <div className="mt-3 pt-2.5 border-t border-zinc-100 dark:border-zinc-800/80 flex items-center justify-between text-xs text-emerald-600 dark:text-emerald-400 font-medium group-hover:underline">
              <span>View Paid Invoices ({paidInvoices.length})</span>
              <ChevronRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition-transform" />
            </div>
          </CardContent>
        </Card>

        {/* Pending Collections */}
        <Card
          onClick={() => {
            setActiveTab('invoices');
            setInvoiceStatusFilter('pending');
          }}
          className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 hover:border-amber-500/50 dark:hover:border-amber-500/50 transition cursor-pointer group shadow-sm hover:shadow"
        >
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
              Pending Collections
            </CardTitle>
            <div className="p-1.5 rounded-md bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400">
              <Clock className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600 dark:text-amber-400">
              ₹{(summary?.total_pending || 0).toLocaleString()}
            </div>
            <p className="text-xs text-zinc-500 mt-1">Outstanding dues across flats</p>
            <div className="mt-3 pt-2.5 border-t border-zinc-100 dark:border-zinc-800/80 flex items-center justify-between text-xs text-amber-600 dark:text-amber-400 font-medium group-hover:underline">
              <span>View Pending Dues ({pendingInvoices.length})</span>
              <ChevronRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition-transform" />
            </div>
          </CardContent>
        </Card>

        {/* Awaiting Approval */}
        <Card
          onClick={() => {
            setActiveTab('approvals');
          }}
          className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 hover:border-indigo-500/50 dark:hover:border-indigo-500/50 transition cursor-pointer group shadow-sm hover:shadow"
        >
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
              Awaiting Approval
            </CardTitle>
            <div className="p-1.5 rounded-md bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400">
              <AlertCircle className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
              {pendingPayments.length}
            </div>
            <p className="text-xs text-zinc-500 mt-1">Offline transfers to verify</p>
            <div className="mt-3 pt-2.5 border-t border-zinc-100 dark:border-zinc-800/80 flex items-center justify-between text-xs text-indigo-600 dark:text-indigo-400 font-medium group-hover:underline">
              <span>Review Verifications ({pendingPayments.length})</span>
              <ChevronRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition-transform" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs Bar */}
      <div className="flex items-center gap-2 border-b border-zinc-200 dark:border-zinc-800">
        <button
          onClick={() => setActiveTab('invoices')}
          className={`pb-3 text-sm font-semibold border-b-2 transition-all px-2 ${
            activeTab === 'invoices'
              ? 'border-zinc-900 text-zinc-900 dark:border-zinc-100 dark:text-zinc-100'
              : 'border-transparent text-zinc-500 hover:text-zinc-900'
          }`}
        >
          Invoices Directory ({invoices.length})
        </button>

        <button
          onClick={() => setActiveTab('approvals')}
          className={`pb-3 text-sm font-semibold border-b-2 transition-all px-2 flex items-center gap-1.5 ${
            activeTab === 'approvals'
              ? 'border-zinc-900 text-zinc-900 dark:border-zinc-100 dark:text-zinc-100'
              : 'border-transparent text-zinc-500 hover:text-zinc-900'
          }`}
        >
          <span>Offline Approvals</span>
          {pendingPayments.length > 0 && (
            <Badge className="bg-amber-500 text-white text-[10px] px-1.5 py-0">
              {pendingPayments.length}
            </Badge>
          )}
        </button>

        <button
          onClick={() => setActiveTab('generate')}
          className={`pb-3 text-sm font-semibold border-b-2 transition-all px-2 ${
            activeTab === 'generate'
              ? 'border-zinc-900 text-zinc-900 dark:border-zinc-100 dark:text-zinc-100'
              : 'border-transparent text-zinc-500 hover:text-zinc-900'
          }`}
        >
          Bulk Invoice Generator
        </button>
      </div>

      {/* Tab 1: Invoices Directory */}
      {activeTab === 'invoices' && (
        <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
          <CardHeader className="py-4 border-b border-zinc-100 dark:border-zinc-800/80">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <div>
                <CardTitle className="text-base font-semibold">Active & Historic Invoices</CardTitle>
                <CardDescription>
                  All maintenance invoices issued across flats in this society with owner & contact details.
                </CardDescription>
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={fetchData}
                disabled={loading}
                className="h-7 text-xs flex items-center gap-1 text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-4">
            {/* Filter Bar & Search */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
              {/* Status Pills */}
              <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
                <Button
                  size="sm"
                  variant={invoiceStatusFilter === 'all' ? 'default' : 'outline'}
                  onClick={() => setInvoiceStatusFilter('all')}
                  className="h-7 text-xs rounded-full px-3"
                >
                  All ({invoices.length})
                </Button>
                <Button
                  size="sm"
                  variant={invoiceStatusFilter === 'pending' ? 'default' : 'outline'}
                  onClick={() => setInvoiceStatusFilter('pending')}
                  className={`h-7 text-xs rounded-full px-3 ${
                    invoiceStatusFilter === 'pending'
                      ? 'bg-amber-600 hover:bg-amber-700 text-white'
                      : 'text-amber-600 dark:text-amber-400 border-amber-300 dark:border-amber-800'
                  }`}
                >
                  Pending ({pendingInvoices.length})
                </Button>
                <Button
                  size="sm"
                  variant={invoiceStatusFilter === 'paid' ? 'default' : 'outline'}
                  onClick={() => setInvoiceStatusFilter('paid')}
                  className={`h-7 text-xs rounded-full px-3 ${
                    invoiceStatusFilter === 'paid'
                      ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                      : 'text-emerald-600 dark:text-emerald-400 border-emerald-300 dark:border-emerald-800'
                  }`}
                >
                  Paid ({paidInvoices.length})
                </Button>
                <Button
                  size="sm"
                  variant={invoiceStatusFilter === 'overdue' ? 'default' : 'outline'}
                  onClick={() => setInvoiceStatusFilter('overdue')}
                  className={`h-7 text-xs rounded-full px-3 ${
                    invoiceStatusFilter === 'overdue'
                      ? 'bg-red-600 hover:bg-red-700 text-white'
                      : 'text-red-600 dark:text-red-400 border-red-300 dark:border-red-800'
                  }`}
                >
                  Overdue ({overdueInvoices.length})
                </Button>
              </div>

              {/* Search Input */}
              <div className="relative w-full sm:w-72">
                <Search className="h-3.5 w-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-400" />
                <Input
                  placeholder="Search flat, wing, resident, title..."
                  value={invoiceSearchQuery}
                  onChange={(e) => setInvoiceSearchQuery(e.target.value)}
                  className="h-8 pl-8 pr-7 text-xs bg-zinc-50 dark:bg-zinc-900"
                />
                {invoiceSearchQuery && (
                  <button
                    onClick={() => setInvoiceSearchQuery('')}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 text-xs"
                    title="Clear search"
                  >
                    ✕
                  </button>
                )}
              </div>
            </div>

            {loading ? (
              <div className="flex justify-center py-16">
                <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
              </div>
            ) : filteredInvoices.length === 0 ? (
              <div className="text-center py-16 border border-dashed rounded-xl border-zinc-200 dark:border-zinc-800 space-y-2">
                <FileText className="h-10 w-10 text-zinc-400 mx-auto" />
                <p className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                  {invoices.length === 0 ? 'No invoices generated yet' : 'No invoices match your filter'}
                </p>
                <p className="text-xs text-zinc-500 max-w-sm mx-auto">
                  {invoices.length === 0
                    ? 'Use the Bulk Invoice Generator to create monthly bills for all society flats.'
                    : 'Try clearing your search query or switching status filters.'}
                </p>
                {invoices.length === 0 ? (
                  <Button
                    size="sm"
                    onClick={() => setActiveTab('generate')}
                    className="mt-2 text-xs"
                  >
                    Generate First Month Bills
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setInvoiceStatusFilter('all');
                      setInvoiceSearchQuery('');
                    }}
                    className="mt-2 text-xs"
                  >
                    Reset Filters
                  </Button>
                )}
              </div>
            ) : (
              <div className="overflow-x-auto rounded-lg border border-zinc-100 dark:border-zinc-800">
                <table className="w-full text-left text-sm">
                  <thead className="bg-zinc-50 dark:bg-zinc-900/50 text-xs text-zinc-500 font-semibold border-b border-zinc-200 dark:border-zinc-800">
                    <tr>
                      <th className="py-3 px-4">Flat / Unit</th>
                      <th className="py-3 px-4">Resident / Owner</th>
                      <th className="py-3 px-4">Period</th>
                      <th className="py-3 px-4">Invoice Title</th>
                      <th className="py-3 px-4">Due Date</th>
                      <th className="py-3 px-4">Amount</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                    {filteredInvoices.map((inv) => (
                      <tr key={inv.id} className="hover:bg-zinc-50/50 dark:hover:bg-zinc-900/30 transition-colors">
                        {/* Flat / Unit */}
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <div className="p-1.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 shrink-0">
                              <Home className="h-3.5 w-3.5" />
                            </div>
                            <div>
                              <div className="font-semibold text-xs text-zinc-900 dark:text-zinc-100">
                                {inv.unit_number ? `Flat ${inv.unit_number}` : 'Unassigned Unit'}
                              </div>
                              <div className="text-[11px] text-zinc-500">
                                {inv.building_name ? `Wing ${inv.building_name}` : 'Main Society'}
                                {inv.floor_number !== undefined && inv.floor_number !== null
                                  ? ` • Floor ${inv.floor_number}`
                                  : ''}
                              </div>
                            </div>
                          </div>
                        </td>

                        {/* Resident / Owner */}
                        <td className="py-3 px-4">
                          <div>
                            <div className="font-medium text-xs text-zinc-900 dark:text-zinc-100 flex items-center gap-1.5">
                              <User className="h-3 w-3 text-zinc-400 shrink-0" />
                              <span>{inv.resident_name || 'Unassigned / Vacant'}</span>
                              {inv.residency_type && (
                                <Badge
                                  variant="outline"
                                  className="text-[9px] px-1 py-0 uppercase font-mono tracking-tight text-zinc-500"
                                >
                                  {inv.residency_type}
                                </Badge>
                              )}
                            </div>
                            {(inv.resident_phone || inv.resident_email) && (
                              <div className="flex items-center gap-2 text-[11px] text-zinc-500 mt-0.5">
                                {inv.resident_phone && (
                                  <a
                                    href={`tel:${inv.resident_phone}`}
                                    className="hover:text-blue-600 dark:hover:text-blue-400 flex items-center gap-0.5"
                                    title="Call resident"
                                  >
                                    <Phone className="h-2.5 w-2.5" />
                                    <span>{inv.resident_phone}</span>
                                  </a>
                                )}
                                {inv.resident_phone && inv.resident_email && <span>•</span>}
                                {inv.resident_email && (
                                  <a
                                    href={`mailto:${inv.resident_email}`}
                                    className="hover:text-blue-600 dark:hover:text-blue-400 flex items-center gap-0.5 truncate max-w-[130px]"
                                    title={inv.resident_email}
                                  >
                                    <Mail className="h-2.5 w-2.5" />
                                    <span className="truncate">{inv.resident_email}</span>
                                  </a>
                                )}
                              </div>
                            )}
                          </div>
                        </td>

                        {/* Period */}
                        <td className="py-3 px-4 font-mono text-xs text-zinc-600 dark:text-zinc-400 whitespace-nowrap">
                          {inv.billing_period}
                        </td>

                        {/* Invoice Title */}
                        <td className="py-3 px-4 font-medium text-xs text-zinc-900 dark:text-zinc-100 max-w-[180px] truncate" title={inv.title}>
                          {inv.title}
                        </td>

                        {/* Due Date */}
                        <td className="py-3 px-4 text-xs text-zinc-500 whitespace-nowrap">
                          {formatDate(inv.due_date)}
                        </td>

                        {/* Amount */}
                        <td className="py-3 px-4 font-semibold text-xs text-zinc-900 dark:text-zinc-100 whitespace-nowrap">
                          ₹{inv.amount.toLocaleString()}
                          {inv.penalty_amount > 0 && (
                            <span className="text-[10px] text-red-500 block font-normal">
                              +₹{inv.penalty_amount.toLocaleString()} late fee
                            </span>
                          )}
                        </td>

                        {/* Status */}
                        <td className="py-3 px-4 whitespace-nowrap">{getStatusBadge(inv.status)}</td>

                        {/* Actions */}
                        <td className="py-3 px-4 text-right whitespace-nowrap">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setViewingInvoice(inv)}
                            className="h-7 text-xs px-2 flex items-center gap-1 ml-auto hover:bg-zinc-100 dark:hover:bg-zinc-800"
                          >
                            <Eye className="h-3 w-3" />
                            <span>View</span>
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 2: Offline Payment Verifications */}
      {activeTab === 'approvals' && (
        <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
          <CardHeader className="py-4 border-b border-zinc-100 dark:border-zinc-800/80">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base font-semibold">Offline Payment Verifications</CardTitle>
                <CardDescription>
                  Review direct bank transfer UTRs, IMPS/NEFT, and cheques submitted by flat owners.
                </CardDescription>
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={fetchData}
                disabled={loading}
                className="h-7 text-xs flex items-center gap-1 text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-4">
            {pendingPayments.length === 0 ? (
              <div className="text-center py-16 border border-dashed rounded-xl border-zinc-200 dark:border-zinc-800 space-y-2">
                <CheckCircle className="h-10 w-10 text-emerald-500 mx-auto" />
                <p className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                  No Pending Verifications
                </p>
                <p className="text-xs text-zinc-500 max-w-sm mx-auto">
                  All submitted offline payments have been reviewed and reconciled.
                </p>
              </div>
            ) : (
              <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {pendingPayments.map((p) => {
                  const isProcessing = actionLoading === p.id;
                  return (
                    <div
                      key={p.id}
                      className="py-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4"
                    >
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-bold text-base text-zinc-900 dark:text-zinc-100">
                            ₹{p.amount.toLocaleString()}
                          </span>
                          <Badge variant="outline" className="text-xs capitalize font-medium">
                            {p.payment_method.replace(/_/g, ' ')}
                          </Badge>
                          {p.invoice_title && (
                            <Badge variant="secondary" className="text-xs font-normal">
                              {p.invoice_title}
                            </Badge>
                          )}
                        </div>

                        {/* Flat & Resident Details */}
                        <div className="flex flex-wrap items-center gap-3 text-xs text-zinc-700 dark:text-zinc-300">
                          <div className="flex items-center gap-1 font-semibold text-zinc-900 dark:text-zinc-100">
                            <Home className="h-3.5 w-3.5 text-zinc-500" />
                            <span>{p.unit_number ? `Flat ${p.unit_number}` : 'Unassigned Unit'}</span>
                            {p.building_name && (
                              <span className="text-zinc-500 font-normal">({p.building_name} Wing)</span>
                            )}
                          </div>
                          <div className="flex items-center gap-1">
                            <User className="h-3.5 w-3.5 text-zinc-400" />
                            <span className="font-medium">{p.user_name || 'Resident'}</span>
                          </div>
                          {p.user_phone && (
                            <a
                              href={`tel:${p.user_phone}`}
                              className="flex items-center gap-1 text-blue-600 dark:text-blue-400 hover:underline"
                            >
                              <Phone className="h-3 w-3" />
                              <span>{p.user_phone}</span>
                            </a>
                          )}
                          {p.user_email && (
                            <a
                              href={`mailto:${p.user_email}`}
                              className="flex items-center gap-1 text-blue-600 dark:text-blue-400 hover:underline truncate max-w-[180px]"
                            >
                              <Mail className="h-3 w-3" />
                              <span className="truncate">{p.user_email}</span>
                            </a>
                          )}
                        </div>

                        <div className="text-xs text-zinc-600 dark:text-zinc-400 font-mono">
                          UTR / Transaction Ref: <span className="font-semibold text-zinc-900 dark:text-zinc-100">{p.transaction_reference || 'N/A'}</span>
                        </div>
                        {p.description && (
                          <p className="text-xs text-zinc-500 italic">&quot;{p.description}&quot;</p>
                        )}
                        <div className="text-[11px] text-zinc-400">
                          Submitted on {formatDateTime(p.created_at)}
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setViewingPayment(p)}
                          className="h-8 text-xs flex items-center gap-1"
                        >
                          <Eye className="h-3.5 w-3.5" />
                          <span>View Proof</span>
                        </Button>

                        <Button
                          size="sm"
                          disabled={isProcessing}
                          onClick={() => handleReviewPayment(p.id, true)}
                          className="bg-emerald-600 hover:bg-emerald-700 text-white h-8 text-xs flex items-center gap-1.5"
                        >
                          {isProcessing ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <CheckCircle className="h-3.5 w-3.5" />
                          )}
                          <span>Approve & Issue Receipt</span>
                        </Button>

                        <Button
                          size="sm"
                          variant="outline"
                          disabled={isProcessing}
                          onClick={() => handleReviewPayment(p.id, false)}
                          className="text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30 border-red-200 dark:border-red-900 h-8 text-xs flex items-center gap-1.5"
                        >
                          <XCircle className="h-3.5 w-3.5" />
                          <span>Reject</span>
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 3: Bulk Invoice Generator Form */}
      {activeTab === 'generate' && (
        <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle className="text-lg font-bold flex items-center gap-2">
              <Building className="h-5 w-5 text-indigo-600" />
              <span>Bulk Monthly Invoice Generator</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Automatically creates and assigns a maintenance bill to every flat in the society for the specified month.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleBulkGenerate} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <Label htmlFor="period" className="text-xs font-medium">
                    Billing Period (YYYY-MM)
                  </Label>
                  <Input
                    id="period"
                    value={bulkPeriod}
                    onChange={(e) => setBulkPeriod(e.target.value)}
                    placeholder="e.g. 2026-10"
                    required
                    className="h-9 text-sm"
                  />
                </div>

                <div className="space-y-1">
                  <Label htmlFor="amount" className="text-xs font-medium">
                    Amount per Flat (₹)
                  </Label>
                  <Input
                    id="amount"
                    type="number"
                    min={1}
                    value={bulkAmount}
                    onChange={(e) => setBulkAmount(parseFloat(e.target.value) || 0)}
                    required
                    className="h-9 text-sm"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <Label htmlFor="title" className="text-xs font-medium">
                  Invoice Title
                </Label>
                <Input
                  id="title"
                  value={bulkTitle}
                  onChange={(e) => setBulkTitle(e.target.value)}
                  placeholder="e.g. Monthly Maintenance - Oct 2026"
                  required
                  className="h-9 text-sm"
                />
              </div>

              <div className="space-y-1">
                <Label htmlFor="dueDays" className="text-xs font-medium">
                  Payment Window (Days until Due Date)
                </Label>
                <Input
                  id="dueDays"
                  type="number"
                  min={1}
                  max={90}
                  value={bulkDueDays}
                  onChange={(e) => setBulkDueDays(parseInt(e.target.value) || 15)}
                  required
                  className="h-9 text-sm"
                />
              </div>

              <div className="space-y-1">
                <Label htmlFor="desc" className="text-xs font-medium">
                  Description & Breakdown
                </Label>
                <Input
                  id="desc"
                  value={bulkDesc}
                  onChange={(e) => setBulkDesc(e.target.value)}
                  placeholder="Line items description"
                  className="h-9 text-sm"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setActiveTab('invoices')}
                  className="h-9 text-xs"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={actionLoading === 'bulk-generate'}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white h-9 text-xs flex items-center gap-1.5 font-semibold"
                >
                  {actionLoading === 'bulk-generate' ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                  <span>Generate All Invoices</span>
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* View Invoice Details Dialog */}
      {viewingInvoice && (
        <Dialog open={!!viewingInvoice} onOpenChange={(open) => !open && setViewingInvoice(null)}>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle className="flex items-center justify-between text-base">
                <span>{viewingInvoice.title}</span>
                {getStatusBadge(viewingInvoice.status)}
              </DialogTitle>
              <DialogDescription className="text-xs">
                Maintenance Invoice Breakdown • Period: {viewingInvoice.billing_period}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-3 py-2 text-sm">
              {/* Resident & Flat Identification Banner */}
              <div className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                    Flat & Resident Details
                  </span>
                  {viewingInvoice.residency_type && (
                    <Badge variant="outline" className="text-[10px] uppercase font-mono">
                      {viewingInvoice.residency_type}
                    </Badge>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-zinc-400 block text-[11px]">Flat & Wing</span>
                    <span className="font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-1 mt-0.5">
                      <Home className="h-3.5 w-3.5 text-zinc-500" />
                      {viewingInvoice.unit_number ? `Flat ${viewingInvoice.unit_number}` : 'Unassigned'}
                      {viewingInvoice.building_name ? ` (${viewingInvoice.building_name})` : ''}
                    </span>
                    {viewingInvoice.floor_number !== undefined && viewingInvoice.floor_number !== null && (
                      <span className="text-[11px] text-zinc-500 block mt-0.5">
                        Floor: {viewingInvoice.floor_number}
                      </span>
                    )}
                  </div>
                  <div>
                    <span className="text-zinc-400 block text-[11px]">Resident / Owner</span>
                    <span className="font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-1 mt-0.5">
                      <User className="h-3.5 w-3.5 text-zinc-500" />
                      {viewingInvoice.resident_name || 'Vacant / Unassigned'}
                    </span>
                  </div>
                </div>

                {(viewingInvoice.resident_phone || viewingInvoice.resident_email) && (
                  <div className="pt-2 border-t border-zinc-200 dark:border-zinc-800 flex flex-wrap items-center gap-3 text-xs">
                    {viewingInvoice.resident_phone && (
                      <a
                        href={`tel:${viewingInvoice.resident_phone}`}
                        className="flex items-center gap-1 text-blue-600 dark:text-blue-400 hover:underline"
                      >
                        <Phone className="h-3 w-3" />
                        <span>{viewingInvoice.resident_phone}</span>
                      </a>
                    )}
                    {viewingInvoice.resident_email && (
                      <a
                        href={`mailto:${viewingInvoice.resident_email}`}
                        className="flex items-center gap-1 text-blue-600 dark:text-blue-400 hover:underline truncate"
                      >
                        <Mail className="h-3 w-3" />
                        <span className="truncate">{viewingInvoice.resident_email}</span>
                      </a>
                    )}
                  </div>
                )}
              </div>

              {/* Amount Box */}
              <div className="p-3 rounded-lg bg-blue-50/50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900 flex items-center justify-between">
                <div>
                  <span className="text-xs text-blue-700 dark:text-blue-400 block">Total Due Amount</span>
                  <span className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
                    ₹{viewingInvoice.amount.toLocaleString()}
                  </span>
                </div>
                {viewingInvoice.penalty_amount > 0 && (
                  <div className="text-right">
                    <span className="text-xs text-red-500 block">Late Fee Penalty</span>
                    <span className="text-xs font-semibold text-red-600">
                      +₹{viewingInvoice.penalty_amount.toLocaleString()}
                    </span>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-2 border-b border-zinc-100 dark:border-zinc-800 pb-2">
                <div>
                  <span className="text-xs text-zinc-500 block">Billing Period</span>
                  <span className="font-semibold text-zinc-900 dark:text-zinc-100 font-mono">
                    {viewingInvoice.billing_period}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-zinc-500 block">Due Date</span>
                  <span className="text-xs text-zinc-700 dark:text-zinc-300 font-medium">
                    {formatDate(viewingInvoice.due_date)}
                  </span>
                </div>
              </div>

              {viewingInvoice.description && (
                <div className="border-b border-zinc-100 dark:border-zinc-800 pb-2">
                  <span className="text-xs text-zinc-500 block">Description / Notes</span>
                  <p className="text-xs text-zinc-600 dark:text-zinc-400 mt-0.5">
                    {viewingInvoice.description}
                  </p>
                </div>
              )}

              <div className="space-y-1">
                <div>
                  <span className="text-xs text-zinc-500 block">Unit Reference ID</span>
                  <span className="font-mono text-[11px] text-zinc-400 break-all">{viewingInvoice.unit_id}</span>
                </div>
                <div>
                  <span className="text-xs text-zinc-500 block">Invoice ID</span>
                  <span className="font-mono text-[11px] text-zinc-400 break-all">{viewingInvoice.id}</span>
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" size="sm" onClick={() => setViewingInvoice(null)} className="h-8 text-xs">
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* View Pending Payment Proof Dialog */}
      {viewingPayment && (
        <Dialog open={!!viewingPayment} onOpenChange={(open) => !open && setViewingPayment(null)}>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle className="flex items-center justify-between text-base">
                <span>Payment Verification</span>
                <Badge variant="outline" className="capitalize text-xs font-semibold">
                  {viewingPayment.payment_method.replace(/_/g, ' ')}
                </Badge>
              </DialogTitle>
              <DialogDescription className="text-xs">
                Resident Offline Payment Submission Record
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-3 py-2 text-sm">
              {/* Resident & Flat Identification */}
              <div className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 space-y-2">
                <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider block">
                  Resident & Flat Info
                </span>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-zinc-400 block text-[11px]">Flat & Wing</span>
                    <span className="font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-1 mt-0.5">
                      <Home className="h-3.5 w-3.5 text-zinc-500" />
                      {viewingPayment.unit_number ? `Flat ${viewingPayment.unit_number}` : 'Unassigned'}
                      {viewingPayment.building_name ? ` (${viewingPayment.building_name})` : ''}
                    </span>
                  </div>
                  <div>
                    <span className="text-zinc-400 block text-[11px]">Submitted By</span>
                    <span className="font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-1 mt-0.5">
                      <User className="h-3.5 w-3.5 text-zinc-500" />
                      {viewingPayment.user_name || 'Resident'}
                    </span>
                  </div>
                </div>

                {(viewingPayment.user_phone || viewingPayment.user_email) && (
                  <div className="pt-2 border-t border-zinc-200 dark:border-zinc-800 flex flex-wrap items-center gap-3 text-xs">
                    {viewingPayment.user_phone && (
                      <a
                        href={`tel:${viewingPayment.user_phone}`}
                        className="flex items-center gap-1 text-blue-600 dark:text-blue-400 hover:underline"
                      >
                        <Phone className="h-3 w-3" />
                        <span>{viewingPayment.user_phone}</span>
                      </a>
                    )}
                    {viewingPayment.user_email && (
                      <a
                        href={`mailto:${viewingPayment.user_email}`}
                        className="flex items-center gap-1 text-blue-600 dark:text-blue-400 hover:underline truncate"
                      >
                        <Mail className="h-3 w-3" />
                        <span className="truncate">{viewingPayment.user_email}</span>
                      </a>
                    )}
                  </div>
                )}
              </div>

              <div className="p-3 rounded-lg bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900 flex items-center justify-between">
                <div>
                  <span className="text-xs text-emerald-700 dark:text-emerald-400 block">Submitted Amount</span>
                  <span className="text-2xl font-bold text-emerald-950 dark:text-emerald-100">
                    ₹{viewingPayment.amount.toLocaleString()}
                  </span>
                </div>
                <Badge className="bg-emerald-600 text-white text-xs">Pending Verification</Badge>
              </div>

              <div className="grid grid-cols-2 gap-2 border-b border-zinc-100 dark:border-zinc-800 pb-2">
                <div>
                  <span className="text-xs text-zinc-500 block">Payment Mode</span>
                  <span className="capitalize font-semibold text-zinc-900 dark:text-zinc-100">
                    {viewingPayment.payment_method.replace(/_/g, ' ')}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-zinc-500 block">Transaction Reference / UTR</span>
                  <span className="font-mono text-xs font-bold text-zinc-900 dark:text-zinc-100">
                    {viewingPayment.transaction_reference || 'N/A'}
                  </span>
                </div>
              </div>

              {viewingPayment.invoice_title && (
                <div className="border-b border-zinc-100 dark:border-zinc-800 pb-2">
                  <span className="text-xs text-zinc-500 block">Associated Invoice</span>
                  <p className="text-xs font-medium text-zinc-800 dark:text-zinc-200 mt-0.5">
                    {viewingPayment.invoice_title}
                  </p>
                </div>
              )}

              {viewingPayment.description && (
                <div className="border-b border-zinc-100 dark:border-zinc-800 pb-2">
                  <span className="text-xs text-zinc-500 block">Resident Note</span>
                  <p className="text-xs text-zinc-600 dark:text-zinc-400 mt-0.5 italic">
                    &quot;{viewingPayment.description}&quot;
                  </p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-2 border-b border-zinc-100 dark:border-zinc-800 pb-2">
                <div>
                  <span className="text-xs text-zinc-500 block">Submission Date</span>
                  <span className="text-xs text-zinc-700 dark:text-zinc-300">
                    {formatDateTime(viewingPayment.created_at)}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-zinc-500 block">Payment ID</span>
                  <span className="font-mono text-[11px] text-zinc-400 break-all">{viewingPayment.id}</span>
                </div>
              </div>
            </div>

            <DialogFooter className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => setViewingPayment(null)} className="h-8 text-xs">
                Close
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  const id = viewingPayment.id;
                  setViewingPayment(null);
                  handleReviewPayment(id, false);
                }}
                className="text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30 border-red-200 dark:border-red-900 h-8 text-xs flex items-center gap-1.5"
              >
                <XCircle className="h-3.5 w-3.5" />
                <span>Reject</span>
              </Button>
              <Button
                size="sm"
                onClick={() => {
                  const id = viewingPayment.id;
                  setViewingPayment(null);
                  handleReviewPayment(id, true);
                }}
                className="bg-emerald-600 hover:bg-emerald-700 text-white h-8 text-xs font-semibold flex items-center gap-1.5"
              >
                <CheckCircle className="h-3.5 w-3.5" />
                <span>Approve & Settle</span>
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* Financial Breakdown Modal */}
      {showFinancialReport && (
        <Dialog open={showFinancialReport} onOpenChange={setShowFinancialReport}>
          <DialogContent className="sm:max-w-xl max-h-[85vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-base">
                <BarChart3 className="h-5 w-5 text-indigo-600" />
                <span>Society Financial & Collection Breakdown</span>
              </DialogTitle>
              <DialogDescription className="text-xs">
                Executive billing summary and outstanding maintenance dues across units.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-2 text-sm">
              {/* Progress & Efficiency */}
              <div className="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-zinc-600 dark:text-zinc-400">Collection Efficiency</span>
                  <span className="text-sm font-bold text-zinc-900 dark:text-zinc-100">
                    {summary?.total_invoiced && summary.total_invoiced > 0
                      ? `${Math.round((summary.total_collected / summary.total_invoiced) * 100)}%`
                      : '0%'}
                  </span>
                </div>
                <div className="w-full bg-zinc-200 dark:bg-zinc-800 h-2.5 rounded-full overflow-hidden">
                  <div
                    className="bg-emerald-600 h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${
                        summary?.total_invoiced && summary.total_invoiced > 0
                          ? Math.min(100, Math.round((summary.total_collected / summary.total_invoiced) * 100))
                          : 0
                      }%`,
                    }}
                  />
                </div>
                <div className="flex justify-between text-[11px] text-zinc-500 pt-1">
                  <span>Collected: ₹{(summary?.total_collected || 0).toLocaleString()}</span>
                  <span>Target: ₹{(summary?.total_invoiced || 0).toLocaleString()}</span>
                </div>
              </div>

              {/* Status Distribution */}
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="p-3 rounded-lg border border-emerald-200 dark:border-emerald-900 bg-emerald-50/50 dark:bg-emerald-950/20">
                  <span className="text-[11px] text-emerald-700 dark:text-emerald-400 block font-medium">Settled / Paid</span>
                  <span className="text-lg font-bold text-emerald-900 dark:text-emerald-200">
                    {paidInvoices.length}
                  </span>
                  <span className="text-[10px] text-zinc-500 block">
                    ₹{paidInvoices.reduce((acc, i) => acc + i.amount, 0).toLocaleString()}
                  </span>
                </div>
                <div className="p-3 rounded-lg border border-amber-200 dark:border-amber-900 bg-amber-50/50 dark:bg-amber-950/20">
                  <span className="text-[11px] text-amber-700 dark:text-amber-400 block font-medium">Pending Dues</span>
                  <span className="text-lg font-bold text-amber-900 dark:text-amber-200">
                    {pendingInvoices.length}
                  </span>
                  <span className="text-[10px] text-zinc-500 block">
                    ₹{pendingInvoices.reduce((acc, i) => acc + i.amount, 0).toLocaleString()}
                  </span>
                </div>
                <div className="p-3 rounded-lg border border-red-200 dark:border-red-900 bg-red-50/50 dark:bg-red-950/20">
                  <span className="text-[11px] text-red-700 dark:text-red-400 block font-medium">Overdue Bills</span>
                  <span className="text-lg font-bold text-red-900 dark:text-red-200">
                    {overdueInvoices.length}
                  </span>
                  <span className="text-[10px] text-zinc-500 block">
                    ₹{overdueInvoices.reduce((acc, i) => acc + i.amount, 0).toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Outstanding Dues by Flat List */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-xs font-semibold text-zinc-700 dark:text-zinc-300">
                    Flats with Outstanding Dues ({pendingInvoices.length + overdueInvoices.length})
                  </h4>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setShowFinancialReport(false);
                      setActiveTab('invoices');
                      setInvoiceStatusFilter('pending');
                    }}
                    className="h-6 text-[11px] text-blue-600 dark:text-blue-400 px-1 hover:underline"
                  >
                    Filter in Directory →
                  </Button>
                </div>
                <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
                  {[...pendingInvoices, ...overdueInvoices].length === 0 ? (
                    <div className="text-center py-6 text-zinc-400 text-xs">
                      All flats are fully settled! Zero outstanding dues.
                    </div>
                  ) : (
                    [...pendingInvoices, ...overdueInvoices].map((inv) => (
                      <div
                        key={inv.id}
                        className="p-2.5 rounded-lg border border-zinc-100 dark:border-zinc-800 flex items-center justify-between text-xs hover:bg-zinc-50 dark:hover:bg-zinc-900/50 transition"
                      >
                        <div className="flex items-center gap-2">
                          <div className="p-1 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300">
                            <Home className="h-3 w-3" />
                          </div>
                          <div>
                            <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                              {inv.unit_number ? `Flat ${inv.unit_number}` : 'Unit'}
                            </span>
                            {inv.building_name && (
                              <span className="text-zinc-400 text-[11px] ml-1">({inv.building_name})</span>
                            )}
                            <div className="text-[11px] text-zinc-500">
                              {inv.resident_name || 'Unassigned'}
                              {inv.resident_phone && ` • ${inv.resident_phone}`}
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <span className="font-bold text-zinc-900 dark:text-zinc-100 block">
                            ₹{inv.amount.toLocaleString()}
                          </span>
                          {getStatusBadge(inv.status)}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" size="sm" onClick={() => setShowFinancialReport(false)} className="h-8 text-xs">
                Close Breakdown
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
