'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/lib/store/auth-store';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Users,
  CheckCircle,
  XCircle,
  Loader2,
  AlertCircle,
  Clock,
  UserCheck,
} from 'lucide-react';

interface PendingRequest {
  membership_id: string;
  user_id: string;
  society_id: string;
  unit_id?: string;
  role: string;
  status: string;
  requested_at?: string;
}

export default function AdminResidentsPage() {
  const user = useAuthStore((state) => state.user);
  const societyId = user?.active_society_id;

  const [requests, setRequests] = useState<PendingRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchRequests = useCallback(async () => {
    if (!societyId) {
      setLoading(false);
      return;
    }

    try {
      const response = await apiClient.get(`/societies/${societyId}/membership/requests`);
      const list = response.data?.data || response.data || [];
      setRequests(Array.isArray(list) ? list : []);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      }
    } finally {
      setLoading(false);
    }
  }, [societyId]);

  useEffect(() => {
    fetchRequests();
  }, [fetchRequests]);

  const handleApprove = async (membershipId: string) => {
    if (!societyId) return;
    setActionLoading(membershipId);
    setFeedback(null);

    try {
      await apiClient.post(`/societies/${societyId}/membership/${membershipId}/approve`);
      setFeedback({ type: 'success', message: 'Resident approved! Verification email sent.' });
      setRequests((prev) => prev.filter((r) => r.membership_id !== membershipId));
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to approve resident request.' });
      }
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (membershipId: string) => {
    if (!societyId) return;
    setActionLoading(membershipId);
    setFeedback(null);

    try {
      await apiClient.post(`/societies/${societyId}/membership/${membershipId}/reject`, {
        reason: 'Unable to verify flat occupancy details.',
      });
      setFeedback({ type: 'success', message: 'Request rejected.' });
      setRequests((prev) => prev.filter((r) => r.membership_id !== membershipId));
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to reject request.' });
      }
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="border-b border-zinc-200 dark:border-zinc-800 pb-4">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 flex items-center gap-2">
          <Users className="h-6 w-6" />
          <span>Resident Approvals Desk</span>
        </h1>
        <p className="text-sm text-zinc-500 mt-1">
          Review and approve pending homeowner and tenant membership applications.
        </p>
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

      {/* Table / List */}
      <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div>
            <CardTitle className="text-base font-semibold">Pending Applications</CardTitle>
            <CardDescription>
              {requests.length} resident{requests.length === 1 ? '' : 's'} awaiting review
            </CardDescription>
          </div>
        </CardHeader>

        <CardContent>
          {loading ? (
            <div className="flex justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
            </div>
          ) : requests.length === 0 ? (
            <div className="text-center py-16 border border-dashed rounded-xl border-zinc-200 dark:border-zinc-800 space-y-2">
              <UserCheck className="h-10 w-10 text-emerald-500 mx-auto" />
              <p className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                All caught up!
              </p>
              <p className="text-xs text-zinc-500 max-w-sm mx-auto">
                There are no pending resident membership requests at this time.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
              {requests.map((req) => {
                const isProcessing = actionLoading === req.membership_id;
                return (
                  <div
                    key={req.membership_id}
                    className="py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                          Applicant (ID: {req.user_id.slice(0, 8)}...)
                        </span>
                        <Badge variant="outline" className="capitalize text-xs font-medium">
                          {req.role}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-zinc-500">
                        <Clock className="h-3.5 w-3.5" />
                        <span>
                          {req.requested_at
                            ? new Date(req.requested_at).toLocaleDateString(undefined, {
                                dateStyle: 'medium',
                              })
                            : 'Recently'}
                        </span>
                        {req.unit_id && <span>• Unit ID: {req.unit_id.slice(0, 8)}</span>}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        disabled={isProcessing}
                        onClick={() => handleApprove(req.membership_id)}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white h-8 text-xs flex items-center gap-1.5"
                      >
                        {isProcessing ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <CheckCircle className="h-3.5 w-3.5" />
                        )}
                        <span>Approve</span>
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={isProcessing}
                        onClick={() => handleReject(req.membership_id)}
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
    </div>
  );
}
