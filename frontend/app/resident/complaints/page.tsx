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
  PlusCircle,
  Loader2,
  AlertCircle,
  CheckCircle,
  Clock,
  Star,
} from 'lucide-react';

interface Complaint {
  id: string;
  ticket_number: string;
  title: string;
  description: string;
  category: string;
  scope: string;
  priority: string;
  status: string;
  sla_deadline: string;
  is_overdue: boolean;
  resolution_notes?: string;
  resident_rating?: number;
  resident_feedback?: string;
  created_at: string;
}

export default function ResidentComplaintsPage() {
  const user = useAuthStore((state) => state.user);
  const societyId = user?.active_society_id;

  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [closeLoading, setCloseLoading] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // New Ticket Form State
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('plumbing');
  const [scope, setScope] = useState('personal_unit');
  const [priority, setPriority] = useState('p3_medium');

  // Rating Modal State
  const [ratingTicketId, setRatingTicketId] = useState<string | null>(null);
  const [rating, setRating] = useState(5);
  const [feedbackText, setFeedbackText] = useState('');

  const fetchMyComplaints = useCallback(async () => {
    if (!societyId) {
      setLoading(false);
      return;
    }

    try {
      const res = await apiClient.get(`/societies/${societyId}/complaints/my`);
      const list = res.data?.data || res.data || [];
      setComplaints(Array.isArray(list) ? list : []);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      }
    } finally {
      setLoading(false);
    }
  }, [societyId]);

  useEffect(() => {
    fetchMyComplaints();
  }, [fetchMyComplaints]);

  // Create Complaint
  const handleCreateComplaint = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!societyId) return;

    setActionLoading(true);
    setFeedback(null);

    try {
      await apiClient.post(`/societies/${societyId}/complaints`, {
        title: title.trim(),
        description: description.trim(),
        category,
        scope,
        priority,
      });

      setFeedback({
        type: 'success',
        message: 'Maintenance ticket created! A technician has been notified.',
      });
      setTitle('');
      setDescription('');
      setShowForm(false);
      await fetchMyComplaints();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to create complaint ticket.' });
      }
    } finally {
      setActionLoading(false);
    }
  };

  // Close & Rate Ticket
  const handleCloseAndRate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!societyId || !ratingTicketId) return;

    setCloseLoading(ratingTicketId);
    setFeedback(null);

    try {
      await apiClient.post(`/societies/${societyId}/complaints/${ratingTicketId}/close`, {
        resident_rating: Number(rating),
        resident_feedback: feedbackText.trim() || undefined,
      });

      setFeedback({ type: 'success', message: 'Thank you! Your feedback has been recorded and ticket closed.' });
      setRatingTicketId(null);
      setFeedbackText('');
      await fetchMyComplaints();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to close ticket.' });
      }
    } finally {
      setCloseLoading(null);
    }
  };

  const getPriorityBadge = (p: string) => {
    switch (p.toLowerCase()) {
      case 'p1_critical':
      case 'p1':
        return <Badge variant="destructive" className="text-[10px]">P1 - 4h SLA</Badge>;
      case 'p2_high':
      case 'p2':
        return <Badge className="bg-amber-600 text-white text-[10px]">P2 - 24h SLA</Badge>;
      case 'p3_medium':
      case 'p3':
        return <Badge variant="outline" className="border-blue-400 text-blue-600 text-[10px]">P3 - 48h SLA</Badge>;
      default:
        return <Badge variant="secondary" className="text-[10px]">P4 - 72h SLA</Badge>;
    }
  };

  const getStatusBadge = (s: string) => {
    switch (s.toLowerCase()) {
      case 'resolved':
        return <Badge className="bg-emerald-600 text-white text-[10px]">RESOLVED</Badge>;
      case 'closed':
        return <Badge variant="secondary" className="text-[10px]">CLOSED</Badge>;
      case 'in_progress':
        return <Badge className="bg-blue-600 text-white text-[10px]">IN PROGRESS</Badge>;
      case 'open':
        return <Badge variant="outline" className="border-amber-500 text-amber-600 text-[10px]">OPEN</Badge>;
      default:
        return <Badge variant="secondary" className="text-[10px]">{s}</Badge>;
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-200 dark:border-zinc-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 flex items-center gap-2">
            <Wrench className="h-6 w-6 text-indigo-600" />
            <span>Helpdesk & Maintenance Complaints</span>
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            Report flat or common area maintenance issues with guaranteed SLA resolution tracking.
          </p>
        </div>

        <Button
          size="sm"
          onClick={() => setShowForm(!showForm)}
          className="bg-indigo-600 hover:bg-indigo-700 text-white h-8 text-xs font-semibold flex items-center gap-1.5"
        >
          <PlusCircle className="h-3.5 w-3.5" />
          <span>Raise Ticket</span>
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

      {/* Raise Ticket Modal Drawer */}
      {showForm && (
        <Card className="border border-indigo-200 dark:border-indigo-900 bg-white dark:bg-zinc-950">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-bold flex items-center gap-2">
              <PlusCircle className="h-5 w-5 text-indigo-600" />
              <span>Raise Maintenance Complaint</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Describe the issue and our society maintenance crew will be dispatched as per SLA.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateComplaint} className="space-y-4">
              <div className="space-y-1">
                <Label htmlFor="ticketTitle" className="text-xs font-medium">
                  Issue Summary
                </Label>
                <Input
                  id="ticketTitle"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Water leakage in kitchen sink pipe"
                  required
                  className="h-9 text-sm"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="space-y-1">
                  <Label htmlFor="category" className="text-xs font-medium">
                    Category
                  </Label>
                  <select
                    id="category"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full h-9 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-3 text-sm"
                  >
                    <option value="plumbing">Plumbing</option>
                    <option value="electrical">Electrical</option>
                    <option value="carpentry">Carpentry</option>
                    <option value="elevator">Elevator / Lift</option>
                    <option value="housekeeping">Housekeeping / Cleaning</option>
                    <option value="security">Security</option>
                    <option value="other">Other Issue</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <Label htmlFor="scope" className="text-xs font-medium">
                    Location Scope
                  </Label>
                  <select
                    id="scope"
                    value={scope}
                    onChange={(e) => setScope(e.target.value)}
                    className="w-full h-9 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-3 text-sm"
                  >
                    <option value="personal_unit">Inside My Flat</option>
                    <option value="common_area">Common Area (Corridor/Lobby)</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <Label htmlFor="priority" className="text-xs font-medium">
                    Urgency (SLA)
                  </Label>
                  <select
                    id="priority"
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full h-9 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-3 text-sm"
                  >
                    <option value="p3_medium">P3 - Medium (48h)</option>
                    <option value="p2_high">P2 - High (24h)</option>
                    <option value="p1_critical">P1 - Critical (4h)</option>
                    <option value="p4_low">P4 - Low (72h)</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1">
                <Label htmlFor="desc" className="text-xs font-medium">
                  Detailed Description
                </Label>
                <textarea
                  id="desc"
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Provide any helpful instructions or specific timings when you are available."
                  required
                  className="w-full rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-3 text-sm"
                />
              </div>

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
                  {actionLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : 'Submit Ticket'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Rate & Close Modal Inline Form */}
      {ratingTicketId && (
        <Card className="border border-emerald-300 dark:border-emerald-900 bg-emerald-50/50 dark:bg-emerald-950/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold text-emerald-950 dark:text-emerald-200">
              Confirm Resolution & Feedback
            </CardTitle>
            <CardDescription className="text-xs">
              Rate the service received to close this maintenance ticket.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCloseAndRate} className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-zinc-700 dark:text-zinc-300">Satisfaction:</span>
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setRating(star)}
                    className="p-1 focus:outline-none"
                  >
                    <Star
                      className={`h-5 w-5 ${
                        star <= rating ? 'text-amber-500 fill-amber-500' : 'text-zinc-300'
                      }`}
                    />
                  </button>
                ))}
              </div>

              <Input
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                placeholder="Optional feedback (e.g. Prompt service, technician was polite)"
                className="h-9 text-sm bg-white dark:bg-zinc-900"
              />

              <div className="flex justify-end gap-2 pt-1">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setRatingTicketId(null)}
                  className="h-8 text-xs"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={closeLoading === ratingTicketId}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white h-8 text-xs font-semibold"
                >
                  {closeLoading === ratingTicketId ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    'Close Ticket'
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Complaints List */}
      <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
        <CardHeader className="py-4">
          <CardTitle className="text-base font-semibold">My Maintenance Requests</CardTitle>
          <CardDescription>
            {complaints.length} ticket{complaints.length === 1 ? '' : 's'} registered under your profile
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
            </div>
          ) : complaints.length === 0 ? (
            <div className="text-center py-16 border border-dashed rounded-xl border-zinc-200 dark:border-zinc-800 space-y-2">
              <CheckCircle className="h-10 w-10 text-emerald-500 mx-auto" />
              <p className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                No tickets reported
              </p>
              <p className="text-xs text-zinc-500 max-w-sm mx-auto">
                Need help with plumbing, electrical, or society repairs? Open a ticket anytime.
              </p>
              <Button
                size="sm"
                onClick={() => setShowForm(true)}
                className="bg-indigo-600 hover:bg-indigo-700 text-white mt-2 text-xs"
              >
                Raise Issue
              </Button>
            </div>
          ) : (
            <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
              {complaints.map((ticket) => {
                const isResolved = ticket.status.toLowerCase() === 'resolved';
                return (
                  <div key={ticket.id} className="py-4 space-y-2">
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
                      </div>

                      {isResolved && (
                        <Button
                          size="sm"
                          onClick={() => setRatingTicketId(ticket.id)}
                          className="bg-emerald-600 hover:bg-emerald-700 text-white h-7 text-xs flex items-center gap-1 font-semibold"
                        >
                          <Star className="h-3 w-3" />
                          <span>Verify & Close</span>
                        </Button>
                      )}
                    </div>

                    <p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
                      {ticket.description}
                    </p>

                    {ticket.resolution_notes && (
                      <div className="p-2.5 rounded-lg bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900 text-xs text-emerald-900 dark:text-emerald-300">
                        <span className="font-semibold">Technician Resolution: </span>
                        {ticket.resolution_notes}
                      </div>
                    )}

                    <div className="flex items-center gap-3 text-[11px] text-zinc-400 pt-1">
                      <span className="capitalize">{ticket.category}</span>
                      <span>• {ticket.scope.replace(/_/g, ' ')}</span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        <span>SLA Deadline: {new Date(ticket.sla_deadline).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
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
