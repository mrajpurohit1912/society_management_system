'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Building2, Loader2, AlertCircle, MailCheck, AlertTriangle } from 'lucide-react';

export default function SignupPage() {
  const router = useRouter();

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [mobileNumber, setMobileNumber] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);
  const [emailSent, setEmailSent] = useState(true);
  const [resending, setResending] = useState(false);
  const [resendStatus, setResendStatus] = useState<string | null>(null);
  const [resendError, setResendError] = useState<string | null>(null);

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

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
      const response = await apiClient.post('/auth/resident/signup', {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim().toLowerCase(),
        password,
        mobile_number: mobileNumber.trim() ? mobileNumber.trim() : undefined,
      });

      const isEmailDelivered = response.data?.email_sent !== false;
      setEmailSent(isEmailDelivered);
      setIsSuccess(true);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to create account. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResendVerification = async () => {
    setResending(true);
    setResendStatus(null);
    setResendError(null);
    try {
      const response = await apiClient.post('/auth/resend-verification', {
        email: email.trim().toLowerCase(),
      });
      setEmailSent(true);
      setResendStatus(response.data?.message || 'Verification email resent successfully! Please check your inbox.');
    } catch (err: unknown) {
      if (err instanceof Error) {
        setResendError(err.message);
      } else {
        setResendError('Failed to resend verification email. Please try again shortly.');
      }
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center items-center px-4 py-12 bg-zinc-50 dark:bg-black font-sans">
      <div className="w-full max-w-md">
        {/* Brand Header */}
        <div className="flex justify-center mb-8">
          <Link href="/" className="flex items-center gap-2 font-bold text-2xl text-zinc-900 dark:text-zinc-50">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-zinc-900 text-white dark:bg-zinc-50 dark:text-zinc-900">
              <Building2 className="h-6 w-6" />
            </div>
            <span>SocietySync</span>
          </Link>
        </div>

        <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 shadow-sm">
          {isSuccess ? (
            /* Success confirmation screen */
            <CardContent className="pt-8 pb-8 text-center space-y-4">
              {emailSent ? (
                <>
                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400">
                    <MailCheck className="h-7 w-7" />
                  </div>
                  <CardTitle className="text-2xl font-bold">Check your email</CardTitle>
                  <CardDescription className="text-sm text-zinc-600 dark:text-zinc-400 max-w-xs mx-auto">
                    We sent a verification link to <strong className="text-zinc-900 dark:text-zinc-100">{email}</strong>. Please check your inbox and click the link to verify your email.
                  </CardDescription>

                  {resendStatus && (
                    <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm">
                      {resendStatus}
                    </div>
                  )}

                  <div className="pt-4 space-y-2">
                    <Button onClick={() => router.push('/login')} className="w-full h-10">
                      Proceed to Sign In
                    </Button>
                    <Button
                      variant="outline"
                      onClick={handleResendVerification}
                      disabled={resending}
                      className="w-full h-10"
                    >
                      {resending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                      {resending ? 'Resending Link...' : "Didn't receive an email? Resend"}
                    </Button>
                  </div>
                </>
              ) : (
                <>
                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400">
                    <AlertTriangle className="h-7 w-7" />
                  </div>
                  <CardTitle className="text-2xl font-bold">Email Delivery Pending</CardTitle>
                  <CardDescription className="text-sm text-zinc-600 dark:text-zinc-400 max-w-xs mx-auto">
                    Your account was created, but we were unable to deliver your verification email to{' '}
                    <strong className="text-zinc-900 dark:text-zinc-100">{email}</strong>. Please click below to resend the verification link.
                  </CardDescription>

                  {resendError && (
                    <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2 text-left">
                      <AlertCircle className="h-4 w-4 shrink-0" />
                      <span>{resendError}</span>
                    </div>
                  )}

                  {resendStatus && (
                    <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm">
                      {resendStatus}
                    </div>
                  )}

                  <div className="pt-4 space-y-2">
                    <Button
                      onClick={handleResendVerification}
                      disabled={resending}
                      className="w-full h-10"
                    >
                      {resending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                      {resending ? 'Resending Link...' : 'Resend Verification Email'}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => router.push('/login')}
                      className="w-full h-10"
                    >
                      Proceed to Sign In
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          ) : (
            /* Signup Form */
            <>
              <CardHeader className="text-center">
                <CardTitle className="text-2xl font-bold">Create Resident Account</CardTitle>
                <CardDescription>Join your residential society community</CardDescription>
              </CardHeader>

              <CardContent>
                {error && (
                  <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    <span>{error}</span>
                  </div>
                )}

                <form onSubmit={handleSignup} className="space-y-4">
                  {/* First & Last Name */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label htmlFor="firstName">First Name</Label>
                      <Input
                        id="firstName"
                        type="text"
                        required
                        placeholder="John"
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="lastName">Last Name</Label>
                      <Input
                        id="lastName"
                        type="text"
                        required
                        placeholder="Doe"
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                      />
                    </div>
                  </div>

                  {/* Email */}
                  <div className="space-y-1.5">
                    <Label htmlFor="email">Email Address</Label>
                    <Input
                      id="email"
                      type="email"
                      required
                      placeholder="name@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                    />
                  </div>

                  {/* Mobile Number (Optional) */}
                  <div className="space-y-1.5">
                    <Label htmlFor="mobile">Mobile Number (Optional)</Label>
                    <Input
                      id="mobile"
                      type="tel"
                      placeholder="+91 98765 43210"
                      value={mobileNumber}
                      onChange={(e) => setMobileNumber(e.target.value)}
                    />
                  </div>

                  {/* Password */}
                  <div className="space-y-1.5">
                    <Label htmlFor="password">Password</Label>
                    <Input
                      id="password"
                      type="password"
                      required
                      placeholder="At least 8 characters"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                    />
                  </div>

                  {/* Confirm Password */}
                  <div className="space-y-1.5">
                    <Label htmlFor="confirmPassword">Confirm Password</Label>
                    <Input
                      id="confirmPassword"
                      type="password"
                      required
                      placeholder="Re-enter password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                    />
                  </div>

                  <Button type="submit" disabled={loading} className="w-full h-10 mt-2">
                    {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                    {loading ? 'Creating Account...' : 'Create Account'}
                  </Button>
                </form>

                <div className="mt-6 text-center text-sm text-zinc-500">
                  Already have an account?{' '}
                  <Link href="/login" className="text-zinc-900 font-semibold underline dark:text-zinc-100">
                    Sign in
                  </Link>
                </div>
              </CardContent>
            </>
          )}
        </Card>
      </div>
    </div>
  );
}