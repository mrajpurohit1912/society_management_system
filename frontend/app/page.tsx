'use client';

import Link from 'next/link';
import { useAuthStore } from '@/lib/store/auth-store';
import { buttonVariants } from '@/components/ui/button';
import {
  Building2,
  QrCode,
  CreditCard,
  Wrench,
  ArrowRight,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';

export default function HomePage() {
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  const getDashboardHref = () => {
    if (!user) return '/login';
    if (user.role === 'platform_admin') return '/platform/dashboard';
    if (user.role === 'society_admin' || user.role === 'committee') return '/admin/dashboard';
    if (user.role === 'resident') {
      if (user.membership_status === 'approved') return '/resident/dashboard';
      if (user.membership_status === 'pending') return '/onboarding/pending-approval';
      return '/onboarding/join-society';
    }
    return '/login';
  };

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-black font-sans text-zinc-900 dark:text-zinc-50 selection:bg-indigo-500 selection:text-white">
      {/* Top Navigation */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-white/80 dark:bg-zinc-950/80 border-b border-zinc-200/80 dark:border-zinc-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="h-9 w-9 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-sm">
              <Building2 className="h-5 w-5" />
            </div>
            <span className="font-extrabold text-lg tracking-tight">SocietySync</span>
          </Link>

          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-zinc-600 dark:text-zinc-400">
            <a href="#features" className="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors">
              Features
            </a>
            <a href="#security" className="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors">
              Gate Security
            </a>
            <a href="#billing" className="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors">
              Billing
            </a>
          </nav>

          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <Link
                href={getDashboardHref()}
                className={buttonVariants({
                  size: 'sm',
                  className: 'bg-indigo-600 hover:bg-indigo-700 text-white font-semibold flex items-center gap-1.5 shadow-sm',
                })}
              >
                <span>Dashboard</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            ) : (
              <>
                <Link
                  href="/login"
                  className={buttonVariants({
                    variant: 'ghost',
                    size: 'sm',
                    className: 'text-sm font-medium',
                  })}
                >
                  Sign In
                </Link>
                <Link
                  href="/register-society"
                  className={buttonVariants({
                    size: 'sm',
                    className: 'bg-indigo-600 hover:bg-indigo-700 text-white font-semibold shadow-sm',
                  })}
                >
                  Register Society
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-28 md:pt-32 md:pb-36">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-8">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-indigo-200 dark:border-indigo-900/60 bg-indigo-50/80 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 text-xs font-semibold">
            <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
            <span>Enterprise Multi-Tenant Residential Platform</span>
          </div>

          {/* Heading */}
          <h1 className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight text-zinc-900 dark:text-zinc-50 leading-[1.1]">
            The Operating System for{' '}
            <span className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
              Modern Gated Communities
            </span>
          </h1>

          {/* Subtitle */}
          <p className="max-w-2xl mx-auto text-base sm:text-lg md:text-xl text-zinc-600 dark:text-zinc-400 leading-relaxed font-normal">
            Automated visitor gate passes with 6-digit OTP, instant maintenance billing, SLA-guaranteed helpdesk tickets, and multi-tenant society governance.
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link
              href="/register-society"
              className={buttonVariants({
                size: 'lg',
                className: 'w-full sm:w-auto bg-indigo-600 hover:bg-indigo-700 text-white font-bold h-12 px-8 text-base shadow-lg shadow-indigo-600/20',
              })}
            >
              Get Started for Your Society
            </Link>

            <Link
              href="/signup"
              className={buttonVariants({
                variant: 'outline',
                size: 'lg',
                className: 'w-full sm:w-auto h-12 px-8 text-base font-semibold border-zinc-300 dark:border-zinc-800',
              })}
            >
              Join as Resident
            </Link>
          </div>

          {/* Social Proof Stats */}
          <div className="pt-12 grid grid-cols-2 sm:grid-cols-4 gap-6 max-w-3xl mx-auto border-t border-zinc-200 dark:border-zinc-800">
            <div>
              <div className="text-2xl sm:text-3xl font-black text-zinc-900 dark:text-zinc-100">100%</div>
              <div className="text-xs text-zinc-500 mt-1">Multi-Tenant Isolation</div>
            </div>
            <div>
              <div className="text-2xl sm:text-3xl font-black text-indigo-600 dark:text-indigo-400">4 Hours</div>
              <div className="text-xs text-zinc-500 mt-1">Critical SLA Response</div>
            </div>
            <div>
              <div className="text-2xl sm:text-3xl font-black text-zinc-900 dark:text-zinc-100">6-Digit</div>
              <div className="text-xs text-zinc-500 mt-1">Instant Gate Passcode</div>
            </div>
            <div>
              <div className="text-2xl sm:text-3xl font-black text-emerald-600 dark:text-emerald-400">Automated</div>
              <div className="text-xs text-zinc-500 mt-1">Receipt Generation</div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Matrix Showcase */}
      <section id="features" className="py-20 bg-white dark:bg-zinc-950 border-y border-zinc-200 dark:border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
          <div className="text-center max-w-2xl mx-auto space-y-3">
            <h2 className="text-xs uppercase font-bold tracking-widest text-indigo-600 dark:text-indigo-400">
              Complete Feature Suite
            </h2>
            <p className="text-3xl sm:text-4xl font-extrabold text-zinc-900 dark:text-zinc-50">
              Everything Your Community Needs to Run Seamlessly
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Card 1 */}
            <div className="p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/30 space-y-4">
              <div className="h-10 w-10 rounded-xl bg-indigo-100 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
                <QrCode className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-bold text-zinc-900 dark:text-zinc-100">
                Visitor Passes & Gate Security
              </h3>
              <p className="text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">
                Residents generate 6-digit entry codes and QR tokens for guests, Swiggy, Zomato, and Uber. Gatekeepers verify with one click.
              </p>
              <ul className="space-y-2 text-xs text-zinc-500 pt-2">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  <span>Configurable validity window (4h - 72h)</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  <span>Real-time overstay and log tracking</span>
                </li>
              </ul>
            </div>

            {/* Card 2 */}
            <div className="p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/30 space-y-4">
              <div className="h-10 w-10 rounded-xl bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                <CreditCard className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-bold text-zinc-900 dark:text-zinc-100">
                Maintenance Billing & Receipts
              </h3>
              <p className="text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">
                One-click bulk billing across all flats. Residents pay via online checkout or submit direct bank transfer UTRs with instant receipt generation.
              </p>
              <ul className="space-y-2 text-xs text-zinc-500 pt-2">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  <span>Automated monthly bulk invoice generator</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  <span>Offline UTR review & approval audit log</span>
                </li>
              </ul>
            </div>

            {/* Card 3 */}
            <div className="p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/30 space-y-4">
              <div className="h-10 w-10 rounded-xl bg-amber-100 dark:bg-amber-950 text-amber-600 dark:text-amber-400 flex items-center justify-center">
                <Wrench className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-bold text-zinc-900 dark:text-zinc-100">
                Helpdesk Tickets & SLA Monitoring
              </h3>
              <p className="text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">
                Report plumbing, electrical, and elevator breakdowns. Built-in SLA engine enforces response deadlines with resident 1-5 star verification.
              </p>
              <ul className="space-y-2 text-xs text-zinc-500 pt-2">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  <span>P1 to P4 prioritization with countdown SLA</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  <span>Technician resolution notes and feedback</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-200 dark:border-zinc-800 py-12 bg-white dark:bg-zinc-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-zinc-500">
          <div className="flex items-center gap-2 font-semibold text-zinc-900 dark:text-zinc-100">
            <Building2 className="h-4 w-4 text-indigo-600" />
            <span>SocietySync Enterprise Residential Cloud</span>
          </div>

          <div className="flex items-center gap-6">
            <Link href="/register-society" className="hover:underline">
              Register Society
            </Link>
            <Link href="/login" className="hover:underline">
              Member Portal
            </Link>
            <Link href="/signup" className="hover:underline">
              Resident Sign Up
            </Link>
          </div>

          <div>&copy; {new Date().getFullYear()} SocietySync Inc. All rights reserved.</div>
        </div>
      </footer>
    </div>
  );
}
