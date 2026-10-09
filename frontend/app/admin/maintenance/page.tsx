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
}

export default function AdminMaintenancePage() {
  const user = useAuthStore((state) => state.user);
  const societyId = user?.active_society_id;

  const [activeTab, setActiveTab] = useState<'invoices' | 'generate' | 'approvals'>('invoices');
  const [summary, setSummary] = useState<CollectionSummary | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [pendingPayments, setPendingPayments] = useState<OfflinePayment[]>([]);
  const [viewingInvoice, setViewingInvoice] = useState<Invoice | null>(null);
  const [viewingPayment, setViewingPayment] = useState<OfflinePayment | null>(null);

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
        return <Badge variant="outline" className="border-amber-500 text-amber-600 text-[10px]">PENDING</Badge>;
      case 'partially_paid':
        return <Badge variant="secondary" className="text-[10px]">PARTIALLY PAID</Badge>;
      default:
        return <Badge variant="outline" className="text-[10px]">{status}</Badge>;
    }
  };

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
            Generate monthly dues, track collections, and verify resident bank transfers.
          </p>
        </div>

        <div className="flex items-center gap-2">
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

      {/* Financial KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
              Total Invoiced
            </CardTitle>
            <DollarSign className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">
              ₹{(summary?.total_invoiced || 0).toLocaleString()}
            </div>
            <p className="text-xs text-zinc-500 mt-1">Total dues issued to residents</p>
          </CardContent>
        </Card>

        <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
              Total Collected
            </CardTitle>
            <CheckCircle className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
              ₹{(summary?.total_collected || 0).toLocaleString()}
            </div>
            <p className="text-xs text-zinc-500 mt-1">Settled payments in account</p>
          </CardContent>
        </Card>

        <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
              Pending Collections
            </CardTitle>
            <Clock className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600 dark:text-amber-400">
              ₹{(summary?.total_pending || 0).toLocaleString()}
            </div>
            <p className="text-xs text-zinc-500 mt-1">Outstanding dues across flats</p>
          </CardContent>
        </Card>

        <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
              Awaiting Approval
            </CardTitle>
            <AlertCircle className="h-4 w-4 text-indigo-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
              {pendingPayments.length}
            </div>
            <p className="text-xs text-zinc-500 mt-1">Offline transfers to verify</p>
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
          <CardHeader className="py-4">
            <CardTitle className="text-base font-semibold">Active & Historic Invoices</CardTitle>
            <CardDescription>All maintenance invoices issued across flats in this society.</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center py-16">
                <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
              </div>
            ) : invoices.length === 0 ? (
              <div className="text-center py-16 border border-dashed rounded-xl border-zinc-200 dark:border-zinc-800 space-y-2">
                <FileText className="h-10 w-10 text-zinc-400 mx-auto" />
                <p className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                  No invoices generated yet
                </p>
                <p className="text-xs text-zinc-500 max-w-sm mx-auto">
                  Use the Bulk Invoice Generator to create monthly bills for all society flats.
                </p>
                <Button
                  size="sm"
                  onClick={() => setActiveTab('generate')}
                  className="mt-2 text-xs"
                >
                  Generate First Month Bills
                </Button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-zinc-50 dark:bg-zinc-900/50 text-xs text-zinc-500 font-semibold border-b border-zinc-200 dark:border-zinc-800">
                    <tr>
                      <th className="py-3 px-4">Period</th>
                      <th className="py-3 px-4">Invoice Title</th>
                      <th className="py-3 px-4">Due Date</th>
                      <th className="py-3 px-4">Amount</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                    {invoices.map((inv) => (
                      <tr key={inv.id} className="hover:bg-zinc-50/50 dark:hover:bg-zinc-900/30">
                        <td className="py-3 px-4 font-mono text-xs text-zinc-600 dark:text-zinc-400">
                          {inv.billing_period}
                        </td>
                        <td className="py-3 px-4 font-medium text-zinc-900 dark:text-zinc-100">
                          {inv.title}
                        </td>
                        <td className="py-3 px-4 text-xs text-zinc-500">
                          {new Date(inv.due_date).toLocaleDateString(undefined, {
                            dateStyle: 'medium',
                          })}
                        </td>
                        <td className="py-3 px-4 font-semibold text-zinc-900 dark:text-zinc-100">
                          ₹{inv.amount.toLocaleString()}
                        </td>
                        <td className="py-3 px-4">{getStatusBadge(inv.status)}</td>
                        <td className="py-3 px-4 text-right">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setViewingInvoice(inv)}
                            className="h-7 text-xs px-2 flex items-center gap-1 ml-auto"
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
          <CardHeader className="py-4">
            <CardTitle className="text-base font-semibold">Offline Payment Verifications</CardTitle>
            <CardDescription>
              Review direct bank transfer UTRs and cheques submitted by residents.
            </CardDescription>
          </CardHeader>
          <CardContent>
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
                      className="py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-base text-zinc-900 dark:text-zinc-100">
                            ₹{p.amount.toLocaleString()}
                          </span>
                          <Badge variant="outline" className="text-xs capitalize font-medium">
                            {p.payment_method.replace(/_/g, ' ')}
                          </Badge>
                        </div>
                        <div className="text-xs text-zinc-600 dark:text-zinc-400 font-mono">
                          UTR / Ref: <span className="font-semibold">{p.transaction_reference || 'N/A'}</span>
                        </div>
                        {p.description && (
                          <p className="text-xs text-zinc-500 italic">&quot;{p.description}&quot;</p>
                        )}
                        <div className="text-[11px] text-zinc-400">
                          Submitted on {new Date(p.created_at).toLocaleString()}
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setViewingPayment(p)}
                          className="h-8 text-xs flex items-center gap-1"
                        >
                          <Eye className="h-3.5 w-3.5" />
                          <span>View</span>
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
          <DialogContent className="sm:max-w-md">
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
              <div className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
                <div>
                  <span className="text-xs text-zinc-500 block">Total Due Amount</span>
                  <span className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
                    ₹{viewingInvoice.amount.toLocaleString()}
                  </span>
                </div>
                {viewingInvoice.penalty_amount > 0 && (
                  <div className="text-right">
                    <span className="text-xs text-red-500 block">Late Fee</span>
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
                    {new Date(viewingInvoice.due_date).toLocaleDateString(undefined, { dateStyle: 'medium' })}
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
          <DialogContent className="sm:max-w-md">
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
                    {new Date(viewingPayment.created_at).toLocaleString()}
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
    </div>
  );
}
