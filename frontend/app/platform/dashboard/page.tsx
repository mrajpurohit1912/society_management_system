'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import { Button, buttonVariants } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  ShieldCheck,
  Building2,
  Users,
  CheckCircle,
  Loader2,
  AlertCircle,
  Sparkles,
  ExternalLink,
  Copy,
  Clock,
  Phone,
  Mail,
} from 'lucide-react';

interface PlatformMetrics {
  total_societies?: number;
  active_subscriptions?: number;
  leads_total?: number;
}

interface SocietyLead {
  lead_id: string;
  organization_name: string;
  primary_contact_name: string;
  email: string;
  mobile: string;
  city: string;
  expected_flats?: number;
  status: string;
  created_at?: string;
}

interface ProvisionedSocietyResult {
  society_id: string;
  society_name: string;
  admin_email: string;
  activation_token: string;
}

export default function PlatformDashboardPage() {
  const [metrics, setMetrics] = useState<PlatformMetrics | null>(null);
  const [leads, setLeads] = useState<SocietyLead[]>([]);
  const [loading, setLoading] = useState(true);
  const [provisionLoading, setProvisionLoading] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [provisionResult, setProvisionResult] = useState<ProvisionedSocietyResult | null>(null);
  const [copiedLink, setCopiedLink] = useState(false);

  const fetchPlatformData = useCallback(async () => {
    try {
      const [metricsRes, leadsRes] = await Promise.allSettled([
        apiClient.get('/platform/dashboard'),
        apiClient.get('/platform/leads'),
      ]);

      if (metricsRes.status === 'fulfilled') {
        setMetrics(metricsRes.value.data?.data || metricsRes.value.data || null);
      }
      if (leadsRes.status === 'fulfilled') {
        const list = leadsRes.value.data?.data || leadsRes.value.data || [];
        setLeads(Array.isArray(list) ? list : []);
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPlatformData();
  }, [fetchPlatformData]);

  // One-Click Auto-Provision from Lead
  const handleProvision = async (leadId: string) => {
    setProvisionLoading(leadId);
    setFeedback(null);
    setProvisionResult(null);

    try {
      const res = await apiClient.post(`/platform/societies/from-lead/${leadId}`);
      const data = res.data?.data || res.data;

      setProvisionResult({
        society_id: data.society_id,
        society_name: data.society_name,
        admin_email: data.admin_email,
        activation_token: data.activation_token,
      });

      setFeedback({
        type: 'success',
        message: `Successfully provisioned ${data.society_name}! Activation email dispatched.`,
      });

      await fetchPlatformData();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to provision society from lead.' });
      }
    } finally {
      setProvisionLoading(null);
    }
  };

  const copyActivationLink = (token: string) => {
    const origin = typeof window !== 'undefined' ? window.location.origin : '';
    const link = `${origin}/activate?token=${token}`;
    navigator.clipboard.writeText(link);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2500);
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="border-b border-zinc-200 dark:border-zinc-800 pb-4">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 flex items-center gap-2">
          <ShieldCheck className="h-6 w-6 text-purple-600" />
          <span>Platform Multi-Tenant Master Console</span>
        </h1>
        <p className="text-sm text-zinc-500 mt-1">
          Review incoming society leads, auto-provision tenant workspaces, and dispatch admin credentials.
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

      {/* Provisioned Success Banner with Activation Token */}
      {provisionResult && (
        <Card className="border-2 border-purple-400 bg-purple-50/50 dark:bg-purple-950/30">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-bold text-purple-950 dark:text-purple-200 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-purple-600" />
              <span>Society Successfully Provisioned: {provisionResult.society_name}</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Tenant workspace created, subscription initiated, and Society Admin account prepared.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="p-3 rounded-lg bg-white dark:bg-zinc-900 border border-purple-200 dark:border-purple-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
              <div>
                <p className="font-semibold text-zinc-900 dark:text-zinc-100">
                  Admin Email: {provisionResult.admin_email}
                </p>
                <p className="text-zinc-500 font-mono text-[11px] mt-0.5">
                  Society ID: {provisionResult.society_id}
                </p>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => copyActivationLink(provisionResult.activation_token)}
                  className="h-8 text-xs flex items-center gap-1.5"
                >
                  <Copy className="h-3.5 w-3.5" />
                  <span>{copiedLink ? 'Copied Link!' : 'Copy Activation Link'}</span>
                </Button>

                <Link
                  href={`/activate?token=${provisionResult.activation_token}`}
                  target="_blank"
                  className={buttonVariants({
                    size: 'sm',
                    className: 'bg-purple-600 hover:bg-purple-700 text-white h-8 text-xs flex items-center gap-1',
                  })}
                >
                  <span>Open Activation</span>
                  <ExternalLink className="h-3 w-3" />
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
              Total Societies
            </CardTitle>
            <Building2 className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-zinc-900 dark:text-zinc-50">
              {metrics?.total_societies ?? 1}
            </div>
            <p className="text-xs text-zinc-500 mt-1">Multi-tenant gated communities</p>
          </CardContent>
        </Card>

        <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
              Active Subscriptions
            </CardTitle>
            <CheckCircle className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400">
              {metrics?.active_subscriptions ?? 1}
            </div>
            <p className="text-xs text-zinc-500 mt-1">Paying enterprise tier tenants</p>
          </CardContent>
        </Card>

        <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
              Registration Inquiries
            </CardTitle>
            <Users className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-blue-600 dark:text-blue-400">
              {leads.length}
            </div>
            <p className="text-xs text-zinc-500 mt-1">Leads awaiting onboarding</p>
          </CardContent>
        </Card>
      </div>

      {/* Leads Management Table */}
      <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
        <CardHeader className="py-4">
          <CardTitle className="text-base font-semibold">Prospective Societies & Inquiries</CardTitle>
          <CardDescription>
            Click &quot;1-Click Auto-Provision&quot; to automatically register the society and email the Admin.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
            </div>
          ) : leads.length === 0 ? (
            <div className="text-center py-16 border border-dashed rounded-xl border-zinc-200 dark:border-zinc-800 space-y-2">
              <Building2 className="h-10 w-10 text-zinc-400 mx-auto" />
              <p className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                No incoming leads right now
              </p>
              <p className="text-xs text-zinc-500 max-w-sm mx-auto">
                Prospective societies submitting the /register-society form will appear here.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
              {leads.map((lead) => {
                const isProvisioned = lead.status === 'provisioned';
                const isProcessing = provisionLoading === lead.lead_id;

                return (
                  <div
                    key={lead.lead_id}
                    className="py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
                  >
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-2">
                        <h2 className="font-bold text-base text-zinc-900 dark:text-zinc-100">
                          {lead.organization_name}
                        </h2>
                        <Badge
                          variant={isProvisioned ? 'default' : 'outline'}
                          className={`text-xs capitalize ${
                            isProvisioned ? 'bg-emerald-600 text-white' : 'text-zinc-500'
                          }`}
                        >
                          {lead.status.replace(/_/g, ' ')}
                        </Badge>
                      </div>

                      <div className="flex items-center gap-3 text-xs text-zinc-500 flex-wrap">
                        <span className="font-medium text-zinc-700 dark:text-zinc-300">
                          {lead.primary_contact_name}
                        </span>
                        <span className="flex items-center gap-1">
                          <Mail className="h-3 w-3" />
                          <span>{lead.email}</span>
                        </span>
                        <span className="flex items-center gap-1">
                          <Phone className="h-3 w-3" />
                          <span>{lead.mobile}</span>
                        </span>
                        <span>• City: {lead.city}</span>
                        {lead.expected_flats && <span>• {lead.expected_flats} Flats</span>}
                      </div>

                      {lead.created_at && (
                        <div className="text-[11px] text-zinc-400 flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          <span>Inquiry on {new Date(lead.created_at).toLocaleDateString()}</span>
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      {isProvisioned ? (
                        <span className="text-emerald-600 text-xs font-semibold flex items-center gap-1">
                          <CheckCircle className="h-4 w-4" />
                          <span>Provisioned</span>
                        </span>
                      ) : (
                        <Button
                          size="sm"
                          disabled={isProcessing}
                          onClick={() => handleProvision(lead.lead_id)}
                          className="bg-purple-600 hover:bg-purple-700 text-white h-8 text-xs font-semibold flex items-center gap-1.5"
                        >
                          {isProcessing ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Sparkles className="h-3.5 w-3.5" />
                          )}
                          <span>1-Click Auto-Provision</span>
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
    </div>
  );
}
