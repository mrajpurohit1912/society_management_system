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
  Bell,
  Pin,
  PlusCircle,
  Trash2,
  Loader2,
  AlertCircle,
  CheckCircle,
  Eye,
  Calendar,
  Sparkles,
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
  read_count?: number;
}

export default function AdminNoticesPage() {
  const user = useAuthStore((state) => state.user);
  const societyId = user?.active_society_id;

  const [notices, setNotices] = useState<Notice[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [viewingNotice, setViewingNotice] = useState<Notice | null>(null);

  // Modal / Form state
  const [showPublishModal, setShowPublishModal] = useState(false);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('general');
  const [priority, setPriority] = useState('normal');
  const [targetAudience, setTargetAudience] = useState('all');
  const [isPinned, setIsPinned] = useState(false);

  const fetchNotices = useCallback(async () => {
    if (!societyId) {
      setLoading(false);
      return;
    }

    try {
      const res = await apiClient.get(`/societies/${societyId}/notices/admin`);
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

  // Publish Notice
  const handlePublish = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!societyId) return;

    setActionLoading(true);
    setFeedback(null);

    try {
      await apiClient.post(`/societies/${societyId}/notices`, {
        title: title.trim(),
        content: content.trim(),
        category,
        priority,
        target_audience: targetAudience,
        is_pinned: isPinned,
      });

      setFeedback({ type: 'success', message: 'Notice successfully broadcasted to society!' });
      setTitle('');
      setContent('');
      setIsPinned(false);
      setShowPublishModal(false);
      await fetchNotices();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to publish notice.' });
      }
    } finally {
      setActionLoading(false);
    }
  };

  // Delete Notice
  const handleDelete = async (noticeId: string) => {
    if (!societyId) return;
    if (!confirm('Are you sure you want to permanently delete this notice?')) return;

    setDeleteLoading(noticeId);
    setFeedback(null);

    try {
      await apiClient.delete(`/societies/${societyId}/notices/${noticeId}`);
      setFeedback({ type: 'success', message: 'Notice deleted successfully.' });
      setNotices((prev) => prev.filter((n) => n.id !== noticeId));
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to delete notice.' });
      }
    } finally {
      setDeleteLoading(null);
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
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-200 dark:border-zinc-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 flex items-center gap-2">
            <Bell className="h-6 w-6" />
            <span>Notice Board & Circulars</span>
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            Broadcast official announcements, AGM circulars, and emergency maintenance alerts.
          </p>
        </div>

        <Button
          size="sm"
          onClick={() => setShowPublishModal(!showPublishModal)}
          className="bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 h-8 text-xs font-semibold flex items-center gap-1.5"
        >
          <PlusCircle className="h-3.5 w-3.5" />
          <span>Publish Notice</span>
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

      {/* Publish Notice Modal Drawer */}
      {showPublishModal && (
        <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-bold flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-indigo-600" />
              <span>Broadcast New Circular</span>
            </CardTitle>
            <CardDescription className="text-xs">
              This message will be instantly visible on all resident dashboards and trigger email notifications.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handlePublish} className="space-y-4">
              <div className="space-y-1">
                <Label htmlFor="noticeTitle" className="text-xs font-medium">
                  Notice Title / Subject
                </Label>
                <Input
                  id="noticeTitle"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Scheduled Lift Maintenance this Saturday"
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
                    <option value="general">General Update</option>
                    <option value="meeting_agm">AGM / Meeting</option>
                    <option value="maintenance">Maintenance & Repairs</option>
                    <option value="emergency">Emergency Alert</option>
                    <option value="event">Festival / Event</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <Label htmlFor="priority" className="text-xs font-medium">
                    Priority
                  </Label>
                  <select
                    id="priority"
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full h-9 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-3 text-sm"
                  >
                    <option value="normal">Normal</option>
                    <option value="urgent">Urgent</option>
                    <option value="low">Low</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <Label htmlFor="target" className="text-xs font-medium">
                    Target Audience
                  </Label>
                  <select
                    id="target"
                    value={targetAudience}
                    onChange={(e) => setTargetAudience(e.target.value)}
                    className="w-full h-9 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-3 text-sm"
                  >
                    <option value="all">All Residents</option>
                    <option value="owners_only">Homeowners Only</option>
                    <option value="tenants_only">Tenants Only</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1">
                <Label htmlFor="content" className="text-xs font-medium">
                  Detailed Notice Description
                </Label>
                <textarea
                  id="content"
                  rows={4}
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Provide all essential details, timelines, contact person, instructions..."
                  required
                  className="w-full rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-3 text-sm"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="pin"
                  checked={isPinned}
                  onChange={(e) => setIsPinned(e.target.checked)}
                  className="rounded border-zinc-300 h-4 w-4"
                />
                <label htmlFor="pin" className="text-xs font-medium text-zinc-700 dark:text-zinc-300">
                  Pin this notice to the top of the resident feed
                </label>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowPublishModal(false)}
                  className="h-8 text-xs"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={actionLoading}
                  className="bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 h-8 text-xs font-semibold"
                >
                  {actionLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : 'Publish Now'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Notices List */}
      <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
        <CardHeader className="py-4">
          <CardTitle className="text-base font-semibold">Broadcast History</CardTitle>
          <CardDescription>
            {notices.length} active announcement{notices.length === 1 ? '' : 's'} across the community
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
            </div>
          ) : notices.length === 0 ? (
            <div className="text-center py-16 border border-dashed rounded-xl border-zinc-200 dark:border-zinc-800 space-y-2">
              <Bell className="h-10 w-10 text-zinc-400 mx-auto" />
              <p className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                No Notices Broadcasted Yet
              </p>
              <p className="text-xs text-zinc-500 max-w-sm mx-auto">
                Keep residents updated with meetings, notices, and society news.
              </p>
              <Button
                size="sm"
                onClick={() => setShowPublishModal(true)}
                className="mt-2 text-xs"
              >
                Create First Notice
              </Button>
            </div>
          ) : (
            <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
              {notices.map((n) => {
                const isDeleting = deleteLoading === n.id;
                return (
                  <div key={n.id} className="py-4 space-y-2">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        {n.is_pinned && (
                          <span className="flex items-center gap-1 text-[11px] font-bold text-amber-600 bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded">
                            <Pin className="h-3 w-3" /> Pinned
                          </span>
                        )}
                        <h2 className="font-bold text-base text-zinc-900 dark:text-zinc-100">
                          {n.title}
                        </h2>
                        {getPriorityBadge(n.priority)}
                        <Badge variant="outline" className="text-[10px] capitalize">
                          {n.category.replace(/_/g, ' ')}
                        </Badge>
                      </div>

                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setViewingNotice(n)}
                          className="h-7 text-xs flex items-center gap-1"
                        >
                          <Eye className="h-3 w-3" />
                          <span>View</span>
                        </Button>
                        <span className="text-xs text-zinc-500 hidden sm:inline">
                          {n.read_count || 0} reads
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={isDeleting}
                          onClick={() => handleDelete(n.id)}
                          className="text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/30 h-7 w-7 p-0"
                        >
                          {isDeleting ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Trash2 className="h-3.5 w-3.5" />
                          )}
                        </Button>
                      </div>
                    </div>

                    <p className="text-xs text-zinc-600 dark:text-zinc-400 whitespace-pre-wrap leading-relaxed">
                      {n.content}
                    </p>

                    <div className="flex items-center gap-3 text-[11px] text-zinc-400 pt-1">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {new Date(n.published_at).toLocaleDateString(undefined, {
                          dateStyle: 'medium',
                        })}
                      </span>
                      <span>• Target: {n.target_audience.replace(/_/g, ' ')}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* View Notice Reader Dialog */}
      {viewingNotice && (
        <Dialog open={!!viewingNotice} onOpenChange={(open) => !open && setViewingNotice(null)}>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <div className="flex items-center gap-2 mb-1">
                {viewingNotice.is_pinned && (
                  <span className="flex items-center gap-1 text-[11px] font-bold text-amber-600 bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded">
                    <Pin className="h-3 w-3" /> Pinned
                  </span>
                )}
                {getPriorityBadge(viewingNotice.priority)}
                <Badge variant="outline" className="text-[10px] capitalize">
                  {viewingNotice.category.replace(/_/g, ' ')}
                </Badge>
              </div>
              <DialogTitle className="text-lg font-bold">
                {viewingNotice.title}
              </DialogTitle>
              <DialogDescription className="text-xs flex items-center gap-2">
                <span>Published on {new Date(viewingNotice.published_at).toLocaleString()}</span>
                <span>• Audience: {viewingNotice.target_audience.replace(/_/g, ' ')}</span>
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-3">
              <div className="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800 text-sm text-zinc-800 dark:text-zinc-200 whitespace-pre-wrap leading-relaxed max-h-[50vh] overflow-y-auto">
                {viewingNotice.content}
              </div>

              <div className="flex items-center justify-between text-xs text-zinc-500 border-t border-zinc-100 dark:border-zinc-800 pt-3">
                <span className="flex items-center gap-1">
                  <Eye className="h-3.5 w-3.5" />
                  <span>{viewingNotice.read_count || 0} residents read this notice</span>
                </span>
                <span className="font-mono text-[11px] text-zinc-400">Notice ID: {viewingNotice.id.slice(0, 8)}...</span>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" size="sm" onClick={() => setViewingNotice(null)} className="h-8 text-xs">
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
