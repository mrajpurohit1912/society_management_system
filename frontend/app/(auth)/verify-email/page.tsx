'use client';

import { useEffect, useState, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Card, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Building2, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const isMissingToken = !token;
  const [loading, setLoading] = useState(!isMissingToken);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(
    isMissingToken ? 'Verification token is missing. Please check the link from your email.' : null
  );

  useEffect(() => {
    if (!token) {
      return;
    }

    let isMounted = true;

    const verify = async () => {
      try {
        await apiClient.post('/auth/verify-email', { token });
        if (isMounted) {
          setSuccess(true);
        }
      } catch (err: unknown) {
        if (isMounted) {
          if (err instanceof Error) {
            setError(err.message);
          } else {
            setError('Failed to verify email. The token may be invalid or expired.');
          }
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    verify();

    return () => {
      isMounted = false;
    };
  }, [token]);

  return (
    <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 shadow-sm">
      {loading && (
        <CardContent className="pt-10 pb-10 text-center space-y-4">
          <Loader2 className="h-10 w-10 animate-spin text-zinc-600 dark:text-zinc-400 mx-auto" />
          <CardTitle className="text-xl font-bold">Verifying your email...</CardTitle>
          <CardDescription>Please wait while we confirm your account credentials.</CardDescription>
        </CardContent>
      )}

      {!loading && success && (
        <CardContent className="pt-10 pb-10 text-center space-y-4">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400">
            <CheckCircle2 className="h-7 w-7" />
          </div>
          <CardTitle className="text-2xl font-bold">Email Verified!</CardTitle>
          <CardDescription className="text-sm text-zinc-600 dark:text-zinc-400 max-w-xs mx-auto">
            Your email has been verified successfully. You can now sign in to your society portal.
          </CardDescription>

          <div className="pt-4">
            <Button onClick={() => router.push('/login')} className="w-full h-10">
              Sign In to Your Account
            </Button>
          </div>
        </CardContent>
      )}

      {!loading && error && (
        <CardContent className="pt-10 pb-10 text-center space-y-4">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-red-50 dark:bg-red-950/50 text-red-600 dark:text-red-400">
            <AlertCircle className="h-7 w-7" />
          </div>
          <CardTitle className="text-2xl font-bold">Verification Failed</CardTitle>
          <CardDescription className="text-sm text-red-600 dark:text-red-400 max-w-xs mx-auto">
            {error}
          </CardDescription>

          <div className="pt-4 flex flex-col gap-2">
            <Button onClick={() => router.push('/login')} variant="outline" className="w-full h-10">
              Back to Sign In
            </Button>
            <Button onClick={() => router.push('/signup')} className="w-full h-10">
              Create New Account
            </Button>
          </div>
        </CardContent>
      )}
    </Card>
  );
}

export default function VerifyEmailPage() {
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
          <VerifyEmailContent />
        </Suspense>
      </div>
    </div>
  );
}
