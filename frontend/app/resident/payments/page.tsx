'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/lib/store/auth-store';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  CreditCard,
  CheckCircle,
  Loader2,
  AlertCircle,
  FileText,
  ShieldCheck,
  Send,
  Building,
  Eye,
  Home,
} from 'lucide-react';

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

interface PaymentReceipt {
  payment_id: string;
  receipt_number: string;
  amount: number;
  date: string;
}

export default function ResidentPaymentsPage() {
  const user = useAuthStore((state) => state.user);
  const societyId = user?.active_society_id;

  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [viewingInvoice, setViewingInvoice] = useState<Invoice | null>(null);

  // Selected invoice for payment
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [paymentMode, setPaymentMode] = useState<'online' | 'offline'>('online');
  const [utrNumber, setUtrNumber] = useState('');
  const [receipt, setReceipt] = useState<PaymentReceipt | null>(null);

  const fetchInvoices = useCallback(async () => {
    if (!societyId) {
      setLoading(false);
      return;
    }

    try {
      const url = user?.unit_id
        ? `/societies/${societyId}/invoices?unit_id=${user.unit_id}`
        : `/societies/${societyId}/invoices`;
      const res = await apiClient.get(url);
      const list = res.data?.data || res.data || [];
      setInvoices(Array.isArray(list) ? list : []);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      }
    } finally {
      setLoading(false);
    }
  }, [societyId, user?.unit_id]);

  useEffect(() => {
    fetchInvoices();
  }, [fetchInvoices]);

  // Online Instant Checkout (Mock Gateway)
  const handleOnlinePayment = async (invoice: Invoice) => {
    if (!societyId) return;

    setActionLoading(invoice.id);
    setFeedback(null);

    try {
      // 1. Initiate order
      const initRes = await apiClient.post(`/societies/${societyId}/payments/initiate`, {
        invoice_id: invoice.id,
        amount: invoice.amount,
        payment_method: 'online_mock',
      });
      const order = initRes.data?.data || initRes.data;

      // 2. Verify and settle order
      const verifyRes = await apiClient.post('/payments/verify', {
        payment_id: order.payment_id,
        gateway_order_id: order.gateway_order_id,
        gateway_payment_id: `pay_mock_${Date.now()}`,
        gateway_signature: 'mock_valid_signature_token',
      });

      const resData = verifyRes.data?.data || verifyRes.data;
      setReceipt({
        payment_id: order.payment_id,
        receipt_number: resData.receipt_number || `REC-${Date.now().toString().slice(-6)}`,
        amount: invoice.amount,
        date: new Date().toLocaleDateString(),
      });

      setFeedback({
        type: 'success',
        message: 'Payment settled instantly! Official society receipt generated.',
      });
      setSelectedInvoice(null);
      await fetchInvoices();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Online payment failed.' });
      }
    } finally {
      setActionLoading(null);
    }
  };

  // Submit Offline Bank Transfer UTR
  const handleOfflinePayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!societyId || !selectedInvoice || !utrNumber.trim()) return;

    setActionLoading(selectedInvoice.id);
    setFeedback(null);

    try {
      await apiClient.post(`/societies/${societyId}/payments/submit-offline`, {
        invoice_id: selectedInvoice.id,
        amount: selectedInvoice.amount,
        payment_method: 'offline_upi_neft',
        transaction_reference: utrNumber.trim(),
        description: `Direct Bank Transfer for ${selectedInvoice.title}`,
      });

      setFeedback({
        type: 'success',
        message: 'Bank transfer reference submitted! Society Admin will verify and issue receipt.',
      });
      setSelectedInvoice(null);
      setUtrNumber('');
      await fetchInvoices();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to submit offline transfer.' });
      }
    } finally {
      setActionLoading(null);
    }
  };

  const pendingInvoices = invoices.filter((inv) => inv.status !== 'paid');
  const totalPendingAmount = pendingInvoices.reduce((sum, inv) => sum + inv.amount, 0);

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'paid':
        return <Badge className="bg-emerald-600 text-white text-[10px]">PAID</Badge>;
      case 'overdue':
        return <Badge variant="destructive" className="text-[10px]">OVERDUE</Badge>;
      case 'pending':
        return <Badge variant="outline" className="border-amber-500 text-amber-600 text-[10px]">PENDING</Badge>;
      default:
        return <Badge variant="secondary" className="text-[10px]">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-200 dark:border-zinc-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 flex items-center gap-2">
            <CreditCard className="h-6 w-6 text-emerald-600" />
            <span>Maintenance Dues & Invoices</span>
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            Review monthly maintenance charges, pay securely online, or submit bank transfer details.
          </p>
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

      {/* Outstanding Summary Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-700 text-white shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <span className="text-xs uppercase font-bold tracking-wider text-emerald-100 flex items-center gap-1.5">
            <Building className="h-4 w-4" />
            <span>Total Outstanding Dues</span>
          </span>
          <div className="text-3xl font-extrabold mt-1">
            ₹{totalPendingAmount.toLocaleString()}
          </div>
          <p className="text-xs text-emerald-100 mt-1">
            {pendingInvoices.length} unpaid maintenance bill{pendingInvoices.length === 1 ? '' : 's'}
          </p>
        </div>

        {pendingInvoices.length > 0 && (
          <Button
            size="sm"
            onClick={() => {
              setSelectedInvoice(pendingInvoices[0]);
              setPaymentMode('online');
            }}
            className="bg-white text-emerald-900 hover:bg-emerald-50 h-9 px-4 text-xs font-bold"
          >
            Pay Next Due Now
          </Button>
        )}
      </div>

      {/* Official Receipt Card (if recently settled) */}
      {receipt && (
        <Card className="border-2 border-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/20">
          <CardHeader className="pb-2 flex flex-row items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-emerald-600" />
              <CardTitle className="text-base font-bold text-emerald-950 dark:text-emerald-200">
                Official Payment Receipt
              </CardTitle>
            </div>
            <Badge className="bg-emerald-600 text-white text-[10px]">VERIFIED & PAID</Badge>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-zinc-700 dark:text-zinc-300">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 font-mono text-xs">
              <div>
                <span className="text-zinc-500 block text-[10px]">Receipt No</span>
                <span className="font-bold">{receipt.receipt_number}</span>
              </div>
              <div>
                <span className="text-zinc-500 block text-[10px]">Amount Paid</span>
                <span className="font-bold">₹{receipt.amount.toLocaleString()}</span>
              </div>
              <div>
                <span className="text-zinc-500 block text-[10px]">Date</span>
                <span>{receipt.date}</span>
              </div>
              <div>
                <span className="text-zinc-500 block text-[10px]">Status</span>
                <span className="text-emerald-600 font-bold">Settled</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Payment Action Modal Drawer */}
      {selectedInvoice && (
        <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 shadow-md">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-bold flex items-center justify-between">
              <span>Checkout: {selectedInvoice.title}</span>
              <span className="text-emerald-600 font-bold text-lg">
                ₹{selectedInvoice.amount.toLocaleString()}
              </span>
            </CardTitle>
            <CardDescription className="text-xs">
              Select your payment method below to complete settlement.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-2 border-b border-zinc-200 dark:border-zinc-800 pb-3">
              <button
                type="button"
                onClick={() => setPaymentMode('online')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                  paymentMode === 'online'
                    ? 'bg-emerald-600 text-white'
                    : 'bg-zinc-100 dark:bg-zinc-900 text-zinc-600 dark:text-zinc-400'
                }`}
              >
                Instant Online Payment (UPI / Cards)
              </button>
              <button
                type="button"
                onClick={() => setPaymentMode('offline')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                  paymentMode === 'offline'
                    ? 'bg-emerald-600 text-white'
                    : 'bg-zinc-100 dark:bg-zinc-900 text-zinc-600 dark:text-zinc-400'
                }`}
              >
                Direct Bank Transfer (UTR / NEFT)
              </button>
            </div>

            {paymentMode === 'online' ? (
              <div className="space-y-3">
                <div className="p-3 rounded-lg bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900 text-xs text-emerald-900 dark:text-emerald-300">
                  <ShieldCheck className="h-4 w-4 inline mr-1 text-emerald-600" />
                  Instant automated settlement with receipt generated directly to your account.
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedInvoice(null)}
                    className="h-8 text-xs"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    disabled={actionLoading === selectedInvoice.id}
                    onClick={() => handleOnlinePayment(selectedInvoice)}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white h-8 text-xs font-semibold flex items-center gap-1.5"
                  >
                    {actionLoading === selectedInvoice.id ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <CreditCard className="h-3.5 w-3.5" />
                    )}
                    <span>Pay ₹{selectedInvoice.amount.toLocaleString()} Online</span>
                  </Button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleOfflinePayment} className="space-y-3">
                <div className="space-y-1">
                  <Label htmlFor="utr" className="text-xs font-medium">
                    Bank Reference / UTR Number
                  </Label>
                  <Input
                    id="utr"
                    value={utrNumber}
                    onChange={(e) => setUtrNumber(e.target.value)}
                    placeholder="e.g. UTR9876543210 or Cheque #123456"
                    required
                    className="h-9 text-sm"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedInvoice(null)}
                    className="h-8 text-xs"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    size="sm"
                    disabled={actionLoading === selectedInvoice.id}
                    className="bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 h-8 text-xs font-semibold flex items-center gap-1.5"
                  >
                    {actionLoading === selectedInvoice.id ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Send className="h-3.5 w-3.5" />
                    )}
                    <span>Submit Transfer Proof</span>
                  </Button>
                </div>
              </form>
            )}
          </CardContent>
        </Card>
      )}

      {/* Invoices List */}
      <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
        <CardHeader className="py-4">
          <CardTitle className="text-base font-semibold">Maintenance Invoices</CardTitle>
          <CardDescription>
            {invoices.length} bill{invoices.length === 1 ? '' : 's'} recorded for your residence
          </CardDescription>
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
                No invoices found
              </p>
              <p className="text-xs text-zinc-500 max-w-sm mx-auto">
                No maintenance invoices have been posted to your account yet.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
              {invoices.map((inv) => {
                const isPaid = inv.status.toLowerCase() === 'paid';
                return (
                  <div
                    key={inv.id}
                    className="py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h2 className="font-bold text-sm text-zinc-900 dark:text-zinc-100">
                          {inv.title}
                        </h2>
                        {getStatusBadge(inv.status)}
                      </div>
                      <div className="flex items-center gap-2 text-xs text-zinc-500">
                        <span className="font-mono">Period: {inv.billing_period}</span>
                        <span>• Due by {new Date(inv.due_date).toLocaleDateString()}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="text-base font-bold text-zinc-900 dark:text-zinc-100">
                        ₹{inv.amount.toLocaleString()}
                      </span>

                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setViewingInvoice(inv)}
                        className="h-8 text-xs font-semibold gap-1.5"
                      >
                        <Eye className="h-3.5 w-3.5 text-zinc-500" />
                        <span>View</span>
                      </Button>

                      {!isPaid && (
                        <Button
                          size="sm"
                          onClick={() => {
                            setSelectedInvoice(inv);
                            setPaymentMode('online');
                          }}
                          className="bg-emerald-600 hover:bg-emerald-700 text-white h-8 text-xs font-semibold"
                        >
                          Pay Now
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* View Invoice Dialog */}
      <Dialog open={!!viewingInvoice} onOpenChange={(open) => !open && setViewingInvoice(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg">
              <FileText className="h-5 w-5 text-emerald-600" />
              Invoice Details
            </DialogTitle>
            <DialogDescription>
              Maintenance bill breakdown and status
            </DialogDescription>
          </DialogHeader>
          {viewingInvoice && (
            <div className="space-y-4 py-2 text-sm">
              <div className="flex justify-between items-center p-3 rounded-lg bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
                <div>
                  <p className="font-semibold text-zinc-900 dark:text-zinc-100">{viewingInvoice.title}</p>
                  <p className="text-xs text-zinc-500 font-mono">Period: {viewingInvoice.billing_period}</p>
                </div>
                {getStatusBadge(viewingInvoice.status)}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800">
                  <span className="text-xs text-zinc-500 block">Total Due</span>
                  <span className="text-lg font-bold text-emerald-600">₹{viewingInvoice.amount.toLocaleString()}</span>
                </div>
                <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800">
                  <span className="text-xs text-zinc-500 block">Due Date</span>
                  <span className="font-semibold text-zinc-900 dark:text-zinc-100">{new Date(viewingInvoice.due_date).toLocaleDateString()}</span>
                </div>
              </div>

              {viewingInvoice.penalty_amount > 0 && (
                <div className="flex justify-between items-center text-xs text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 p-2.5 rounded-lg border border-amber-200 dark:border-amber-800">
                  <span>Late Penalty Fee:</span>
                  <span className="font-bold">₹{viewingInvoice.penalty_amount.toLocaleString()}</span>
                </div>
              )}

              {viewingInvoice.description && (
                <div className="space-y-1">
                  <span className="text-xs text-zinc-500 font-medium">Description</span>
                  <p className="text-xs text-zinc-700 dark:text-zinc-300 p-2.5 rounded-lg bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
                    {viewingInvoice.description}
                  </p>
                </div>
              )}

              <div className="text-xs text-zinc-500 space-y-1 pt-1">
                <div className="flex justify-between">
                  <span>Invoice ID:</span>
                  <span className="font-mono text-[11px]">{viewingInvoice.id}</span>
                </div>
                <div className="flex justify-between">
                  <span>Generated On:</span>
                  <span>{new Date(viewingInvoice.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              <DialogFooter className="pt-2 flex sm:justify-between items-center">
                <Button variant="outline" size="sm" onClick={() => setViewingInvoice(null)}>
                  Close
                </Button>
                {viewingInvoice.status.toLowerCase() !== 'paid' && (
                  <Button
                    size="sm"
                    className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold"
                    onClick={() => {
                      const inv = viewingInvoice;
                      setViewingInvoice(null);
                      setSelectedInvoice(inv);
                      setPaymentMode('online');
                    }}
                  >
                    Pay Now
                  </Button>
                )}
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
