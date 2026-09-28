'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Building2, Loader2, CheckCircle2, AlertCircle, Sparkles } from 'lucide-react';

export default function RegisterSocietyPage() {
  const router = useRouter();

  const [orgName, setOrgName] = useState('');
  const [contactName, setContactName] = useState('');
  const [email, setEmail] = useState('');
  const [mobile, setMobile] = useState('');
  const [city, setCity] = useState('');
  const [expectedFlats, setExpectedFlats] = useState<number>(100);
  const [comments, setComments] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await apiClient.post('/register-society', {
        organization_name: orgName.trim(),
        primary_contact_name: contactName.trim(),
        email: email.trim().toLowerCase(),
        mobile: mobile.trim(),
        city: city.trim(),
        expected_flats: Number(expectedFlats) || 100,
        comments: comments.trim() ? comments.trim() : undefined,
      });

      setIsSuccess(true);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to submit society inquiry. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center items-center px-4 py-12 bg-zinc-50 dark:bg-black font-sans">
      <div className="w-full max-w-lg">
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
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400">
                <CheckCircle2 className="h-7 w-7" />
              </div>
              <CardTitle className="text-2xl font-bold">Inquiry Received!</CardTitle>
              <CardDescription className="text-sm text-zinc-600 dark:text-zinc-400 max-w-sm mx-auto">
                Thank you for registering <strong className="text-zinc-900 dark:text-zinc-100">{orgName}</strong>. Our onboarding team has received your details and sent a confirmation to <strong className="text-zinc-900 dark:text-zinc-100">{email}</strong>.
              </CardDescription>

              <div className="pt-4 flex flex-col gap-2">
                <Button onClick={() => router.push('/')} className="w-full h-10">
                  Return to Home
                </Button>
                <Button onClick={() => router.push('/login')} variant="outline" className="w-full h-10">
                  Already have an account? Sign In
                </Button>
              </div>
            </CardContent>
          ) : (
            /* Society Enquiry Form */
            <>
              <CardHeader className="text-center">
                <div className="inline-flex items-center justify-center gap-1.5 px-3 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 text-xs font-medium text-zinc-800 dark:text-zinc-200 mx-auto mb-2">
                  <Sparkles className="h-3.5 w-3.5" />
                  <span>Onboard Your Community</span>
                </div>
                <CardTitle className="text-2xl font-bold">Register Your Society</CardTitle>
                <CardDescription>Digitize notices, visitor check-ins, maintenance payments, and complaints</CardDescription>
              </CardHeader>

              <CardContent>
                {error && (
                  <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    <span>{error}</span>
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                  {/* Society Name */}
                  <div className="space-y-1.5">
                    <Label htmlFor="orgName">Society / Complex Name</Label>
                    <Input
                      id="orgName"
                      type="text"
                      required
                      placeholder="e.g. Palm Meadows Residency"
                      value={orgName}
                      onChange={(e) => setOrgName(e.target.value)}
                    />
                  </div>

                  {/* Contact Name & Mobile */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label htmlFor="contactName">Contact Person Name</Label>
                      <Input
                        id="contactName"
                        type="text"
                        required
                        placeholder="e.g. Rahul Sharma"
                        value={contactName}
                        onChange={(e) => setContactName(e.target.value)}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="mobile">Mobile Number</Label>
                      <Input
                        id="mobile"
                        type="tel"
                        required
                        placeholder="+91 98765 43210"
                        value={mobile}
                        onChange={(e) => setMobile(e.target.value)}
                      />
                    </div>
                  </div>

                  {/* Email & City */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label htmlFor="email">Official Email Address</Label>
                      <Input
                        id="email"
                        type="email"
                        required
                        placeholder="secretary@example.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="city">City</Label>
                      <Input
                        id="city"
                        type="text"
                        required
                        placeholder="e.g. Mumbai"
                        value={city}
                        onChange={(e) => setCity(e.target.value)}
                      />
                    </div>
                  </div>

                  {/* Approximate Flats */}
                  <div className="space-y-1.5">
                    <Label htmlFor="expectedFlats">Estimated Units / Flats</Label>
                    <Input
                      id="expectedFlats"
                      type="number"
                      min={1}
                      required
                      value={expectedFlats}
                      onChange={(e) => setExpectedFlats(Number(e.target.value))}
                    />
                  </div>

                  {/* Comments / Notes */}
                  <div className="space-y-1.5">
                    <Label htmlFor="comments">Additional Notes (Optional)</Label>
                    <Input
                      id="comments"
                      type="text"
                      placeholder="e.g. 3 towers, active RWA"
                      value={comments}
                      onChange={(e) => setComments(e.target.value)}
                    />
                  </div>

                  <Button type="submit" disabled={loading} className="w-full h-10 mt-2">
                    {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                    {loading ? 'Submitting Registration...' : 'Submit Society Registration'}
                  </Button>
                </form>

                <div className="mt-6 text-center text-sm text-zinc-500">
                  Are you a resident looking for your flat?{' '}
                  <Link href="/signup" className="text-zinc-900 font-semibold underline dark:text-zinc-100">
                    Sign up as Resident
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
