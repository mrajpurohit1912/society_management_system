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
  Wrench,
  CheckCircle,
  Clock,
  AlertTriangle,
  Loader2,
  AlertCircle,
  User,
  CheckSquare,
} from 'lucide-react';

interface ComplaintMetrics {
  total_tickets: number;
  open_tickets: number;
  assigned_tickets: number;
  in_progress_tickets: number;
  resolved_tickets: number;
  closed_tickets: number;
  overdue_sla_tickets: number;
  average_rating?: number;
}

interface ComplaintTicket {
  id: string;
  society_id: string;
  unit_id?: string;
  ticket_number: string;
  title: string;
  description: string;
  category: string;
  scope: string;
  priority: string;
  status: string;
  common_area_location?: string;
  sla_deadline: string;
  is_overdue: boolean;
  assigned_vendor_name?: string;
  resolution_notes?: string;
  created_at: string;
}

export default function AdminComplaintsPage() {
  const user = useAuthStore((state) => state.user);
  const societyId = user?.active_society_id;

  const [metrics, setMetrics] = useState<ComplaintMetrics | null>(null);
  const [tickets, setTickets] = useState<ComplaintTicket[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Resolution modal state
  const [resolvingTicketId, setResolvingTicketId] = useState<string | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState('');

  const fetchData = useCallback(async () => {
    if (!societyId) {
      setLoading(false);
      return;
    }

    try {
      const [metricsRes, ticketsRes] = await Promise.allSettled([
        apiClient.get(`/societies/${societyId}/complaints/summary`),
        apiClient.get(`/societies/${societyId}/complaints`),
      ]);

      if (metricsRes.status === 'fulfilled') {
        setMetrics(metricsRes.value.data?.data || metricsRes.value.data || null);
      }
      if (ticketsRes.status === 'fulfilled') {
        const list = ticketsRes.value.data?.data || ticketsRes.value.data || [];
        setTickets(Array.isArray(list) ? list : []);
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

  // Set status to in_progress
  const handleMarkInProgress = async (ticketId: string) => {
    if (!societyId) return;

    setActionLoading(ticketId);
    setFeedback(null);

    try {
      await apiClient.patch(`/societies/${societyId}/complaints/${ticketId}/status`, {
        status: 'in_progress',
        notes: 'Technician dispatched to investigate.',
      });
      setFeedback({ type: 'success', message: 'Ticket moved to In Progress.' });
      await fetchData();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to update ticket status.' });
      }
    } finally {
      setActionLoading(null);
    }
  };

  // Submit resolution
  const handleResolveTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!societyId || !resolvingTicketId) return;

    setActionLoading(resolvingTicketId);
    setFeedback(null);

    try {
      await apiClient.post(`/societies/${societyId}/complaints/${resolvingTicketId}/resolve`, {
        resolution_notes: resolutionNotes.trim(),
      });
      setFeedback({ type: 'success', message: 'Ticket resolved successfully! Resident notified.' });
      setResolvingTicketId(null);
      setResolutionNotes('');
      await fetchData();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to resolve ticket.' });
      }
    } finally {
      setActionLoading(null);
    }
  };

  const filteredTickets = tickets.filter((t) => {
    if (statusFilter === 'all') return true;
    return t.status.toLowerCase() === statusFilter;
  });

  const getPriorityBadge = (p: string) => {
    switch (p.toLowerCase()) {
      case 'p1_critical':
      case 'p1':
        return <Badge variant="destructive" className="text-[10px]">P1 - CRITICAL</Badge>;
      case 'p2_high':
      case 'p2':
        return <Badge className="bg-amber-600 text-white text-[10px]">P2 - HIGH</Badge>;
      case 'p3_medium':
      case 'p3':
        return <Badge variant="outline" className="border-blue-400 text-blue-600 text-[10px]">P3 - MEDIUM</Badge>;
      default:
        return <Badge variant="secondary" className="text-[10px]">{p}</Badge>;
    }
  };

  const getStatusBadge = (s: string) => {
    switch (s.toLowerCase()) {
      case 'resolved':
      case 'closed':
        return <Badge className="bg-emerald-600 text-white text-[10px]">RESOLVED</Badge>;
      case 'in_progress':
        return <Badge className="bg-blue-600 text-white text-[10px]">IN PROGRESS</Badge>;
      case 'open':
        return <Badge variant="outline" className="border-amber-500 text-amber-600 text-[10px]">OPEN</Badge>;
      default:
        return <Badge variant="secondary" className="text-[10px]">{s}</Badge>;
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-200 dark:border-zinc-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 flex items-center gap-2">
            <Wrench className="h-6 w-6" />
            <span>Helpdesk & Maintenance Complaints</span>
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            Track SLA deadlines, assign vendors, and resolve resident service tickets.
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

      {/* SLA & Metrics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <Card className="border border-zinc-200 dark:border-zinc-800 p-3 bg-white dark:bg-zinc-950">
          <p className="text-[11px] font-semibold text-zinc-500 uppercase">Total Tickets</p>
          <p className="text-xl font-bold text-zinc-900 dark:text-zinc-50 mt-1">{metrics?.total_tickets || 0}</p>
        </Card>
        <Card className="border border-zinc-200 dark:border-zinc-800 p-3 bg-white dark:bg-zinc-950">
          <p className="text-[11px] font-semibold text-zinc-500 uppercase">Open</p>
          <p className="text-xl font-bold text-amber-600 dark:text-amber-400 mt-1">{metrics?.open_tickets || 0}</p>
        </Card>
        <Card className="border border-zinc-200 dark:border-zinc-800 p-3 bg-white dark:bg-zinc-950">
          <p className="text-[11px] font-semibold text-zinc-500 uppercase">In Progress</p>
          <p className="text-xl font-bold text-blue-600 dark:text-blue-400 mt-1">{metrics?.in_progress_tickets || 0}</p>
        </Card>
        <Card className="border border-zinc-200 dark:border-zinc-800 p-3 bg-white dark:bg-zinc-950">
          <p className="text-[11px] font-semibold text-zinc-500 uppercase">Resolved</p>
          <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">{metrics?.resolved_tickets || 0}</p>
        </Card>
        <Card className="border border-zinc-200 dark:border-zinc-800 p-3 bg-white dark:bg-zinc-950">
          <p className="text-[11px] font-semibold text-zinc-500 uppercase">SLA Breaches</p>
          <p className="text-xl font-bold text-red-600 dark:text-red-400 mt-1">{metrics?.overdue_sla_tickets || 0}</p>
        </Card>
        <Card className="border border-zinc-200 dark:border-zinc-800 p-3 bg-white dark:bg-zinc-950">
          <p className="text-[11px] font-semibold text-zinc-500 uppercase">Satisfaction</p>
          <p className="text-xl font-bold text-indigo-600 dark:text-indigo-400 mt-1">
            {metrics?.average_rating ? `${metrics.average_rating.toFixed(1)} ★` : '5.0 ★'}
          </p>
        </Card>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 border-b border-zinc-200 dark:border-zinc-800">
        {['all', 'open', 'in_progress', 'resolved'].map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-colors ${
              statusFilter === s
                ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900'
                : 'text-zinc-500 hover:text-zinc-900'
            }`}
          >
            {s.replace(/_/g, ' ')}
          </button>
        ))}
      </div>

      {/* Resolve Modal / Inline Form */}
      {resolvingTicketId && (
        <Card className="border border-emerald-300 dark:border-emerald-900 bg-emerald-50/50 dark:bg-emerald-950/20">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-bold text-emerald-950 dark:text-emerald-200 flex items-center gap-1.5">
              <CheckSquare className="h-4 w-4 text-emerald-600" />
              <span>Mark Ticket as Resolved</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Provide resolution notes explaining the maintenance work or repairs performed.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleResolveTicket} className="space-y-3">
              <div className="space-y-1">
                <Label htmlFor="resNotes" className="text-xs font-medium">
                  Resolution Summary
                </Label>
                <Input
                  id="resNotes"
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  placeholder="e.g. Replaced faulty circuit breaker in main distribution box."
                  required
                  className="h-9 text-sm bg-white dark:bg-zinc-900"
                />
              </div>

              <div className="flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setResolvingTicketId(null)}
                  className="h-8 text-xs"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={actionLoading === resolvingTicketId}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white h-8 text-xs font-semibold"
                >
                  {actionLoading === resolvingTicketId ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    'Confirm Resolution'
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Tickets List */}
      <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
        <CardHeader className="py-4">
          <CardTitle className="text-base font-semibold">Service Tickets Queue</CardTitle>
          <CardDescription>
            Showing {filteredTickets.length} ticket{filteredTickets.length === 1 ? '' : 's'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
            </div>
          ) : filteredTickets.length === 0 ? (
            <div className="text-center py-16 border border-dashed rounded-xl border-zinc-200 dark:border-zinc-800 space-y-2">
              <CheckCircle className="h-10 w-10 text-emerald-500 mx-auto" />
              <p className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                No tickets matching current filter
              </p>
              <p className="text-xs text-zinc-500 max-w-sm mx-auto">
                Great job! All issues are being handled in accordance with SLA deadlines.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
              {filteredTickets.map((ticket) => {
                const isProcessing = actionLoading === ticket.id;
                const isResolved = ticket.status === 'resolved' || ticket.status === 'closed';
                return (
                  <div key={ticket.id} className="py-4 space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono text-xs font-bold text-zinc-500">
                          {ticket.ticket_number}
                        </span>
                        <h2 className="font-bold text-sm text-zinc-900 dark:text-zinc-100">
                          {ticket.title}
                        </h2>
                        {getPriorityBadge(ticket.priority)}
                        {getStatusBadge(ticket.status)}
                        {ticket.is_overdue && (
                          <span className="flex items-center gap-1 text-[10px] text-red-600 font-bold bg-red-50 dark:bg-red-950/40 px-1.5 py-0.5 rounded">
                            <AlertTriangle className="h-3 w-3" /> SLA BREACH
                          </span>
                        )}
                      </div>

                      {!isResolved && (
                        <div className="flex items-center gap-2">
                          {ticket.status === 'open' && (
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={isProcessing}
                              onClick={() => handleMarkInProgress(ticket.id)}
                              className="h-7 text-xs"
                            >
                              Mark In Progress
                            </Button>
                          )}
                          <Button
                            size="sm"
                            disabled={isProcessing}
                            onClick={() => {
                              setResolvingTicketId(ticket.id);
                              setResolutionNotes('');
                            }}
                            className="bg-emerald-600 hover:bg-emerald-700 text-white h-7 text-xs flex items-center gap-1"
                          >
                            <CheckCircle className="h-3 w-3" />
                            <span>Resolve</span>
                          </Button>
                        </div>
                      )}
                    </div>

                    <p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
                      {ticket.description}
                    </p>

                    {ticket.resolution_notes && (
                      <div className="p-2.5 rounded-lg bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900 text-xs text-emerald-900 dark:text-emerald-300">
                        <span className="font-semibold">Resolution Notes: </span>
                        {ticket.resolution_notes}
                      </div>
                    )}

                    <div className="flex items-center gap-4 text-[11px] text-zinc-400 flex-wrap pt-1">
                      <span className="capitalize">Category: {ticket.category}</span>
                      <span>• Scope: {ticket.scope.replace(/_/g, ' ')}</span>
                      {ticket.assigned_vendor_name && (
                        <span className="flex items-center gap-1 text-zinc-600 dark:text-zinc-300">
                          <User className="h-3 w-3" /> Assigned to: {ticket.assigned_vendor_name}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        SLA Due: {new Date(ticket.sla_deadline).toLocaleTimeString(undefined, {
                          hour: '2-digit',
                          minute: '2-digit',
                          day: 'numeric',
                          month: 'short',
                        })}
                      </span>
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
