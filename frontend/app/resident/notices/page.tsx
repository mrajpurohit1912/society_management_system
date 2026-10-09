'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/lib/store/auth-store';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Bell,
  Pin,
  Calendar,
  CheckCircle,
  Loader2,
  AlertCircle,
  Eye,
} from 'lucide-react';

interface Notice {
  id: string;
  society_id: string;
  title: string;
  content: string;
  category: string;
  priority: string;
  target_audience: string;
  is_pinned: boolean;
  published_at: string;
  is_read_by_me?: boolean;
}

export default function ResidentNoticesPage() {
  const user = useAuthStore((state) => state.user);
  const societyId = user?.active_society_id;

  const [notices, setNotices] = useState<Notice[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [viewingNotice, setViewingNotice] = useState<Notice | null>(null);

  const fetchNotices = useCallback(async () => {
    if (!societyId) {
      setLoading(false);
      return;
    }

    try {
      const res = await apiClient.get(`/societies/${societyId}/notices`);
      const list = res.data?.data || res.data || [];
      setNotices(Array.isArray(list) ? list : []);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      }
    } finally {
      setLoading(false);
    }
  }, [societyId]);

  useEffect(() => {
    fetchNotices();
  }, [fetchNotices]);

  // Mark notice as read
  const handleMarkRead = async (noticeId: string) => {
    if (!societyId) return;

    setActionLoading(noticeId);
    try {
      await apiClient.post(`/societies/${societyId}/notices/${noticeId}/read`);
      setNotices((prev) =>
        prev.map((n) => (n.id === noticeId ? { ...n, is_read_by_me: true } : n))
      );
    } catch {
      // Graceful fallback
    } finally {
      setActionLoading(null);
    }
  };

  const getPriorityBadge = (p: string) => {
    switch (p.toLowerCase()) {
      case 'urgent':
        return <Badge variant="destructive" className="text-[10px]">URGENT</Badge>;
      case 'normal':
        return <Badge variant="outline" className="border-blue-400 text-blue-600 text-[10px]">NORMAL</Badge>;
      default:
        return <Badge variant="secondary" className="text-[10px] capitalize">{p}</Badge>;
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="border-b border-zinc-200 dark:border-zinc-800 pb-4">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 flex items-center gap-2">
          <Bell className="h-6 w-6 text-indigo-600" />
          <span>Society Notice Board</span>
        </h1>
        <p className="text-sm text-zinc-500 mt-1">
          Official society announcements, general body circulars, and community updates.
        </p>
      </div>

      {/* Feedback Banner */}
      {feedback && (
        <div className="p-3.5 rounded-lg text-sm flex items-center gap-2 border bg-red-50 border-red-200 text-red-800 dark:bg-red-950/50 dark:border-red-900 dark:text-red-300">
          <AlertCircle className="h-4 w-4 shrink-0 text-red-600" />
          <span>{feedback.message}</span>
        </div>
      )}

      {/* Notices Feed */}
      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
        </div>
      ) : notices.length === 0 ? (
        <Card className="border border-dashed border-zinc-300 dark:border-zinc-800 text-center py-16">
          <Bell className="h-10 w-10 text-zinc-400 mx-auto mb-2" />
          <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
            No active notices
          </h2>
          <p className="text-xs text-zinc-500 max-w-sm mx-auto mt-1">
            Check back later for AGM updates, festive circulars, and maintenance schedules.
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          {notices.map((notice) => {
            const isRead = notice.is_read_by_me;
            const isProcessing = actionLoading === notice.id;

            return (
              <Card
                key={notice.id}
                className={`border transition-all bg-white dark:bg-zinc-950 ${
                  notice.is_pinned
                    ? 'border-amber-300 dark:border-amber-800 shadow-sm'
                    : 'border-zinc-200 dark:border-zinc-800'
                }`}
              >
                <CardHeader className="py-4 px-5 pb-3">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      {notice.is_pinned && (
                        <span className="flex items-center gap-1 text-[11px] font-bold text-amber-700 bg-amber-50 dark:bg-amber-950/50 px-2 py-0.5 rounded">
                          <Pin className="h-3 w-3" /> Pinned
                        </span>
                      )}
                      <CardTitle className="text-base font-bold text-zinc-900 dark:text-zinc-100">
                        {notice.title}
                      </CardTitle>
                      {getPriorityBadge(notice.priority)}
                      <Badge variant="outline" className="text-[10px] capitalize">
                        {notice.category.replace(/_/g, ' ')}
                      </Badge>
                    </div>

                    <div className="flex items-center gap-2 text-xs text-zinc-400">
                      <Calendar className="h-3.5 w-3.5" />
                      <span>{new Date(notice.published_at).toLocaleDateString(undefined, { dateStyle: 'medium' })}</span>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="px-5 pb-4 space-y-4">
                  <p className="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed whitespace-pre-wrap">
                    {notice.content}
                  </p>

                  <div className="flex items-center justify-between pt-2 border-t border-zinc-100 dark:border-zinc-800 text-xs">
                    <span className="text-zinc-400">
                      Audience: {notice.target_audience.replace(/_/g, ' ')}
                    </span>

                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setViewingNotice(notice)}
                        className="h-7 text-xs flex items-center gap-1.5"
                      >
                        <Eye className="h-3 w-3" />
                        <span>View</span>
                      </Button>

                      {isRead ? (
                        <span className="text-emerald-600 font-medium flex items-center gap-1">
                          <CheckCircle className="h-3.5 w-3.5" />
                          <span>Acknowledged</span>
                        </span>
                      ) : (
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={isProcessing}
                          onClick={() => handleMarkRead(notice.id)}
                          className="h-7 text-xs flex items-center gap-1"
                        >
                          {isProcessing ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <CheckCircle className="h-3 w-3" />
                          )}
                          <span>Mark as Read</span>
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* View Notice Dialog */}
      <Dialog open={!!viewingNotice} onOpenChange={(open) => !open && setViewingNotice(null)}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              {viewingNotice?.is_pinned && (
                <span className="flex items-center gap-1 text-[11px] font-bold text-amber-700 bg-amber-50 dark:bg-amber-950/50 px-2 py-0.5 rounded">
                  <Pin className="h-3 w-3" /> Pinned
                </span>
              )}
              {viewingNotice && getPriorityBadge(viewingNotice.priority)}
              <Badge variant="outline" className="text-[10px] capitalize">
                {viewingNotice?.category.replace(/_/g, ' ')}
              </Badge>
            </div>
            <DialogTitle className="text-lg font-bold text-zinc-900 dark:text-zinc-100">
              {viewingNotice?.title}
            </DialogTitle>
            <DialogDescription className="flex items-center gap-2 text-xs text-zinc-400">
              <Calendar className="h-3.5 w-3.5" />
              <span>
                Published on {viewingNotice && new Date(viewingNotice.published_at).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })}
              </span>
            </DialogDescription>
          </DialogHeader>

          {viewingNotice && (
            <div className="space-y-4 py-2 text-sm">
              <div className="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800 text-zinc-700 dark:text-zinc-300 leading-relaxed whitespace-pre-wrap">
                {viewingNotice.content}
              </div>

              <div className="flex items-center justify-between text-xs text-zinc-400 p-2.5 rounded-lg border border-zinc-200 dark:border-zinc-800">
                <span>Audience: <strong className="text-zinc-700 dark:text-zinc-300 capitalize">{viewingNotice.target_audience.replace(/_/g, ' ')}</strong></span>
                <span>Notice ID: <code className="font-mono text-[11px]">{viewingNotice.id}</code></span>
              </div>

              <DialogFooter className="pt-2 flex sm:justify-between items-center">
                <Button variant="outline" size="sm" onClick={() => setViewingNotice(null)}>
                  Close
                </Button>
                {!viewingNotice.is_read_by_me && (
                  <Button
                    size="sm"
                    className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold flex items-center gap-1.5"
                    onClick={() => {
                      handleMarkRead(viewingNotice.id);
                      setViewingNotice({ ...viewingNotice, is_read_by_me: true });
                    }}
                  >
                    <CheckCircle className="h-3.5 w-3.5" />
                    <span>Acknowledge Notice</span>
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
