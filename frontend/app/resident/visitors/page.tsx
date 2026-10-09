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
  QrCode,
  PlusCircle,
  Loader2,
  AlertCircle,
  CheckCircle,
  Copy,
  Clock,
  Car,
  Package,
  ShieldCheck,
  Trash2,
  Eye,
} from 'lucide-react';

interface VisitorPass {
  id: string;
  society_id: string;
  unit_id: string;
  visitor_name: string;
  visitor_phone: string;
  visitor_type: string;
  passcode: string;
  qr_code_token: string;
  valid_from: string;
  valid_until: string;
  status: string;
  vehicle_number?: string;
  expected_delivery_company?: string;
  created_at: string;
}

export default function ResidentVisitorsPage() {
  const user = useAuthStore((state) => state.user);
  const societyId = user?.active_society_id;

  const [passes, setPasses] = useState<VisitorPass[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [revokeLoading, setRevokeLoading] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [viewingPass, setViewingPass] = useState<VisitorPass | null>(null);

  // New Pass Generator Form State
  const [showForm, setShowForm] = useState(false);
  const [visitorName, setVisitorName] = useState('');
  const [visitorPhone, setVisitorPhone] = useState('');
  const [visitorType, setVisitorType] = useState('guest');
  const [validHours, setValidHours] = useState(12);
  const [vehicleNumber, setVehicleNumber] = useState('');
  const [deliveryCompany, setDeliveryCompany] = useState('');
  const [copiedPasscode, setCopiedPasscode] = useState<string | null>(null);

  const fetchPasses = useCallback(async () => {
    if (!societyId) {
      setLoading(false);
      return;
    }

    try {
      const res = await apiClient.get(`/societies/${societyId}/visitor-passes`);
      const list = res.data?.data || res.data || [];
      setPasses(Array.isArray(list) ? list : []);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      }
    } finally {
      setLoading(false);
    }
  }, [societyId]);

  useEffect(() => {
    fetchPasses();
  }, [fetchPasses]);

  // Create Visitor Pass
  const handleCreatePass = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!societyId) return;

    setActionLoading(true);
    setFeedback(null);

    try {
      const res = await apiClient.post(`/societies/${societyId}/visitor-passes`, {
        unit_id: user?.unit_id || undefined,
        visitor_name: visitorName.trim(),
        visitor_phone: visitorPhone.trim(),
        visitor_type: visitorType,
        valid_hours: Number(validHours),
        vehicle_number: vehicleNumber.trim() || undefined,
        expected_delivery_company: deliveryCompany.trim() || undefined,
      });

      const newPass = res.data?.data || res.data;
      setFeedback({
        type: 'success',
        message: `Pass created! Security Gate Passcode: ${newPass.passcode}`,
      });
      setVisitorName('');
      setVisitorPhone('');
      setVehicleNumber('');
      setDeliveryCompany('');
      setShowForm(false);
      await fetchPasses();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to generate visitor pass.' });
      }
    } finally {
      setActionLoading(false);
    }
  };

  // Revoke Pass
  const handleRevokePass = async (passId: string) => {
    if (!societyId) return;

    setRevokeLoading(passId);
    setFeedback(null);

    try {
      await apiClient.delete(`/societies/${societyId}/visitor-passes/${passId}`);
      setFeedback({ type: 'success', message: 'Visitor pass revoked successfully.' });
      await fetchPasses();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to revoke visitor pass.' });
      }
    } finally {
      setRevokeLoading(null);
    }
  };

  const copyToClipboard = (passcode: string) => {
    navigator.clipboard.writeText(passcode);
    setCopiedPasscode(passcode);
    setTimeout(() => setCopiedPasscode(null), 2500);
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return <Badge className="bg-emerald-600 text-white text-[10px]">ACTIVE</Badge>;
      case 'checked_in':
        return <Badge className="bg-blue-600 text-white text-[10px]">INSIDE SOCIETY</Badge>;
      case 'checked_out':
        return <Badge variant="secondary" className="text-[10px]">CHECKED OUT</Badge>;
      case 'expired':
        return <Badge variant="outline" className="text-[10px] text-zinc-400">EXPIRED</Badge>;
      case 'revoked':
        return <Badge variant="destructive" className="text-[10px]">REVOKED</Badge>;
      default:
        return <Badge variant="outline" className="text-[10px]">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-200 dark:border-zinc-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 flex items-center gap-2">
            <QrCode className="h-6 w-6 text-indigo-600" />
            <span>Visitor Gate Passes</span>
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            Pre-approve guests, food deliveries, cabs, and service staff for seamless gate security entry.
          </p>
        </div>

        <Button
          size="sm"
          onClick={() => setShowForm(!showForm)}
          className="bg-indigo-600 hover:bg-indigo-700 text-white h-8 text-xs font-semibold flex items-center gap-1.5"
        >
          <PlusCircle className="h-3.5 w-3.5" />
          <span>New Visitor Pass</span>
        </Button>
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

      {/* Pass Generation Modal Drawer */}
      {showForm && (
        <Card className="border border-indigo-200 dark:border-indigo-900 bg-white dark:bg-zinc-950">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-bold flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-indigo-600" />
              <span>Pre-Approve Visitor Entry</span>
            </CardTitle>
            <CardDescription className="text-xs">
              A 6-digit passcode will be generated for the visitor to share at the security checkpoint.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreatePass} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <Label htmlFor="visitorName" className="text-xs font-medium">
                    Visitor Full Name
                  </Label>
                  <Input
                    id="visitorName"
                    value={visitorName}
                    onChange={(e) => setVisitorName(e.target.value)}
                    placeholder="e.g. Rahul Sharma"
                    required
                    className="h-9 text-sm"
                  />
                </div>

                <div className="space-y-1">
                  <Label htmlFor="visitorPhone" className="text-xs font-medium">
                    Visitor Phone Number
                  </Label>
                  <Input
                    id="visitorPhone"
                    value={visitorPhone}
                    onChange={(e) => setVisitorPhone(e.target.value)}
                    placeholder="e.g. +919876543210"
                    required
                    className="h-9 text-sm"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="space-y-1">
                  <Label htmlFor="visitorType" className="text-xs font-medium">
                    Visitor Category
                  </Label>
                  <select
                    id="visitorType"
                    value={visitorType}
                    onChange={(e) => setVisitorType(e.target.value)}
                    className="w-full h-9 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-3 text-sm"
                  >
                    <option value="guest">Personal Guest</option>
                    <option value="delivery">Delivery (Food/Parcel)</option>
                    <option value="cab">Cab / Taxi (Uber/Ola)</option>
                    <option value="service">Home Service / Maintenance</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <Label htmlFor="validHours" className="text-xs font-medium">
                    Valid Duration
                  </Label>
                  <select
                    id="validHours"
                    value={validHours}
                    onChange={(e) => setValidHours(parseInt(e.target.value) || 12)}
                    className="w-full h-9 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-3 text-sm"
                  >
                    <option value={4}>4 Hours</option>
                    <option value={8}>8 Hours</option>
                    <option value={12}>12 Hours (Default)</option>
                    <option value={24}>24 Hours (Full Day)</option>
                    <option value={72}>3 Days</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <Label htmlFor="vehNum" className="text-xs font-medium">
                    Vehicle Number (Optional)
                  </Label>
                  <Input
                    id="vehNum"
                    value={vehicleNumber}
                    onChange={(e) => setVehicleNumber(e.target.value)}
                    placeholder="e.g. MH02CD5678"
                    className="h-9 text-sm"
                  />
                </div>
              </div>

              {visitorType === 'delivery' && (
                <div className="space-y-1">
                  <Label htmlFor="company" className="text-xs font-medium">
                    Delivery App / Provider
                  </Label>
                  <Input
                    id="company"
                    value={deliveryCompany}
                    onChange={(e) => setDeliveryCompany(e.target.value)}
                    placeholder="e.g. Swiggy, Zomato, Amazon, Blinkit"
                    className="h-9 text-sm"
                  />
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowForm(false)}
                  className="h-8 text-xs"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={actionLoading}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white h-8 text-xs font-semibold"
                >
                  {actionLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : 'Generate Passcode'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Active Passes List */}
      <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
        <CardHeader className="py-4">
          <CardTitle className="text-base font-semibold">Your Passes & Gate Approvals</CardTitle>
          <CardDescription>
            {passes.length} entry pass{passes.length === 1 ? '' : 'es'} created for your unit
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
            </div>
          ) : passes.length === 0 ? (
            <div className="text-center py-16 border border-dashed rounded-xl border-zinc-200 dark:border-zinc-800 space-y-2">
              <QrCode className="h-10 w-10 text-zinc-400 mx-auto" />
              <p className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                No active gate passes
              </p>
              <p className="text-xs text-zinc-500 max-w-sm mx-auto">
                Expecting a friend or delivery? Create a pass to allow instant gate check-in.
              </p>
              <Button
                size="sm"
                onClick={() => setShowForm(true)}
                className="bg-indigo-600 hover:bg-indigo-700 text-white mt-2 text-xs"
              >
                Create Gate Pass
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {passes.map((pass) => {
                const isRevoking = revokeLoading === pass.id;
                const isActive = pass.status === 'active';
                return (
                  <div
                    key={pass.id}
                    className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50/40 dark:bg-zinc-900/30 flex flex-col justify-between space-y-3"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <h2 className="font-bold text-base text-zinc-900 dark:text-zinc-100">
                            {pass.visitor_name}
                          </h2>
                          {getStatusBadge(pass.status)}
                        </div>
                        <p className="text-xs text-zinc-500 mt-0.5">{pass.visitor_phone}</p>
                      </div>

                      {isActive && (
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={isRevoking}
                          onClick={() => handleRevokePass(pass.id)}
                          className="text-red-500 hover:text-red-700 h-7 text-xs px-2"
                        >
                          {isRevoking ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Trash2 className="h-3.5 w-3.5" />
                          )}
                        </Button>
                      )}
                    </div>

                    {/* Passcode Card */}
                    <div className="p-3 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 border border-indigo-200 dark:border-indigo-900 flex items-center justify-between">
                      <div>
                        <span className="text-[10px] uppercase font-bold text-indigo-700 dark:text-indigo-400 block tracking-wider">
                          Security Gate Passcode
                        </span>
                        <span className="font-mono text-2xl font-black text-indigo-950 dark:text-indigo-100 tracking-widest">
                          {pass.passcode}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setViewingPass(pass)}
                          className="h-8 text-xs bg-white dark:bg-zinc-900 flex items-center gap-1.5"
                        >
                          <Eye className="h-3.5 w-3.5" />
                          <span>View</span>
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => copyToClipboard(pass.passcode)}
                          className="h-8 text-xs bg-white dark:bg-zinc-900 flex items-center gap-1.5"
                        >
                          <Copy className="h-3.5 w-3.5" />
                          <span>{copiedPasscode === pass.passcode ? 'Copied!' : 'Copy OTP'}</span>
                        </Button>
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-zinc-500 pt-1 border-t border-zinc-100 dark:border-zinc-800">
                      <span className="capitalize flex items-center gap-1">
                        {pass.visitor_type === 'delivery' ? (
                          <Package className="h-3 w-3" />
                        ) : (
                          <Car className="h-3 w-3" />
                        )}
                        <span>{pass.visitor_type}</span>
                        {pass.vehicle_number && <span>({pass.vehicle_number})</span>}
                      </span>

                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        <span>Expires {new Date(pass.valid_until).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* View Pass Details Dialog */}
      <Dialog open={!!viewingPass} onOpenChange={(open) => !open && setViewingPass(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg">
              <QrCode className="h-5 w-5 text-indigo-600" />
              Visitor Gate Pass Details
            </DialogTitle>
            <DialogDescription>
              Security gate passcode and visitor verification details
            </DialogDescription>
          </DialogHeader>
          {viewingPass && (
            <div className="space-y-4 py-2 text-sm">
              <div className="p-4 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 border border-indigo-200 dark:border-indigo-900 text-center space-y-1">
                <span className="text-[11px] uppercase font-bold text-indigo-700 dark:text-indigo-400 block tracking-wider">
                  6-Digit Gate Passcode
                </span>
                <span className="font-mono text-3xl font-black text-indigo-950 dark:text-indigo-100 tracking-widest block">
                  {viewingPass.passcode}
                </span>
                <p className="text-[11px] text-zinc-500 pt-1">
                  Visitor should share this code at the security checkpoint.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800">
                  <span className="text-xs text-zinc-500 block">Visitor Name</span>
                  <span className="font-semibold text-zinc-900 dark:text-zinc-100">{viewingPass.visitor_name}</span>
                </div>
                <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800">
                  <span className="text-xs text-zinc-500 block">Phone Number</span>
                  <span className="font-semibold text-zinc-900 dark:text-zinc-100">{viewingPass.visitor_phone}</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800">
                  <span className="text-xs text-zinc-500 block">Category</span>
                  <span className="font-semibold capitalize text-zinc-900 dark:text-zinc-100">{viewingPass.visitor_type}</span>
                </div>
                <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800">
                  <span className="text-xs text-zinc-500 block">Status</span>
                  <div className="mt-0.5">{getStatusBadge(viewingPass.status)}</div>
                </div>
              </div>

              {viewingPass.vehicle_number && (
                <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
                  <span className="text-xs text-zinc-500">Vehicle Number</span>
                  <span className="font-mono font-bold text-zinc-900 dark:text-zinc-100">{viewingPass.vehicle_number}</span>
                </div>
              )}

              {viewingPass.expected_delivery_company && (
                <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
                  <span className="text-xs text-zinc-500">Delivery Service</span>
                  <span className="font-medium text-zinc-900 dark:text-zinc-100">{viewingPass.expected_delivery_company}</span>
                </div>
              )}

              <div className="text-xs text-zinc-500 space-y-1.5 p-3 rounded-lg bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
                <div className="flex justify-between">
                  <span>Valid From:</span>
                  <span>{new Date(viewingPass.valid_from).toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Valid Until:</span>
                  <span className="font-medium text-zinc-900 dark:text-zinc-100">{new Date(viewingPass.valid_until).toLocaleString()}</span>
                </div>
                <div className="flex justify-between pt-1 border-t border-zinc-200 dark:border-zinc-800">
                  <span>Pass ID:</span>
                  <span className="font-mono text-[11px]">{viewingPass.id}</span>
                </div>
              </div>

              <DialogFooter className="pt-2 flex sm:justify-between items-center">
                <Button variant="outline" size="sm" onClick={() => setViewingPass(null)}>
                  Close
                </Button>
                <Button
                  size="sm"
                  className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold flex items-center gap-1.5"
                  onClick={() => copyToClipboard(viewingPass.passcode)}
                >
                  <Copy className="h-3.5 w-3.5" />
                  <span>{copiedPasscode === viewingPass.passcode ? 'Copied!' : 'Copy Passcode'}</span>
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
