'use client';

import { useState, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Building2, Loader2, CheckCircle2, AlertCircle, ShieldCheck } from 'lucide-react';

function ActivateAccountContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(
    !token ? 'Activation token is missing. Please use the activation link sent to your email.' : null
  );
  const [isSuccess, setIsSuccess] = useState(false);

  const handleActivate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!token) {
      setError('Activation token is missing. Please check your email link.');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match. Please re-enter your password.');
      return;
    }

    setLoading(true);

    try {
      await apiClient.post('/auth/activate', {
        token,
        password,
      });

      setIsSuccess(true);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to activate account. The activation token may be invalid or expired.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 shadow-sm">
      {isSuccess ? (
        /* Success Screen */
        <CardContent className="pt-8 pb-8 text-center space-y-4">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400">
            <CheckCircle2 className="h-7 w-7" />
          </div>
          <CardTitle className="text-2xl font-bold">Admin Account Activated!</CardTitle>
          <CardDescription className="text-sm text-zinc-600 dark:text-zinc-400 max-w-xs mx-auto">
            Your administrator password has been set successfully. You can now access your society management portal.
          </CardDescription>

          <div className="pt-4">
            <Button onClick={() => router.push('/login')} className="w-full h-10">
              Sign In as Administrator
            </Button>
          </div>
        </CardContent>
      ) : (
        /* Password Setup Form */
        <>
          <CardHeader className="text-center">
            <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <CardTitle className="text-2xl font-bold">Activate Admin Account</CardTitle>
            <CardDescription>Set your password to complete setup for your society</CardDescription>
          </CardHeader>

          <CardContent>
            {error && (
              <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleActivate} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="password">New Password</Label>
                <Input
                  id="password"
                  type="password"
                  required
                  placeholder="At least 8 characters"
                  disabled={!token || loading}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  required
                  placeholder="Re-enter password"
                  disabled={!token || loading}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </div>

              <Button type="submit" disabled={!token || loading} className="w-full h-10 mt-2">
                {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                {loading ? 'Activating Account...' : 'Set Password & Activate'}
              </Button>
            </form>

            <div className="mt-6 text-center text-sm text-zinc-500">
              Already activated?{' '}
              <Link href="/login" className="text-zinc-900 font-semibold underline dark:text-zinc-100">
                Sign in
              </Link>
            </div>
          </CardContent>
        </>
      )}
    </Card>
  );
}

export default function ActivatePage() {
  return (
    <div className="min-h-screen flex flex-col justify-center items-center px-4 py-12 bg-zinc-50 dark:bg-black font-sans">
      <div className="w-full max-w-md">
        <div className="flex justify-center mb-8">
          <Link href="/" className="flex items-center gap-2 font-bold text-2xl text-zinc-900 dark:text-zinc-50">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-zinc-900 text-white dark:bg-zinc-50 dark:text-zinc-900">
              <Building2 className="h-6 w-6" />
            </div>
            <span>SocietySync</span>
          </Link>
        </div>

        <Suspense
          fallback={
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-zinc-500" />
            </div>
          }
        >
          <ActivateAccountContent />
        </Suspense>
      </div>
    </div>
  );
}
