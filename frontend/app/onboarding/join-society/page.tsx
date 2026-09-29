'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/lib/store/auth-store';
import { AuthGuard } from '@/components/auth/auth-guard';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Building2, Search, Loader2, CheckCircle, AlertCircle, LogOut, MapPin } from 'lucide-react';

interface SocietyItem {
  id: string;
  name: string;
  city: string;
  state: string;
  address: string;
}

function JoinSocietyContent() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const setMembership = useAuthStore((state) => state.setMembership);

  const [societies, setSocieties] = useState<SocietyItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSocietyId, setSelectedSocietyId] = useState<string | null>(null);
  const [role, setRole] = useState<'resident' | 'tenant'>('resident');

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const fetchSocieties = async () => {
      try {
        const response = await apiClient.get('/societies');
        if (isMounted) {
          const list = response.data?.data || response.data || [];
          setSocieties(Array.isArray(list) ? list : []);
        }
      } catch (err: unknown) {
        if (isMounted) {
          if (err instanceof Error) {
            setError(err.message);
          } else {
            setError('Failed to load registered societies. Please refresh the page.');
          }
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchSocieties();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleJoin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSocietyId) {
      setError('Please select a society from the list.');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await apiClient.post('/societies/membership/request', {
        society_id: selectedSocietyId,
        role,
      });

      // Synchronize Zustand Auth state to pending
      setMembership(selectedSocietyId, role, 'pending');

      // Navigate to the waiting / pending approval screen
      router.replace('/onboarding/pending-approval');
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to submit membership request. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const filteredSocieties = societies.filter((s) => {
    const term = searchTerm.toLowerCase();
    return (
      s.name?.toLowerCase().includes(term) ||
      s.city?.toLowerCase().includes(term) ||
      s.address?.toLowerCase().includes(term)
    );
  });

  return (
    <div className="min-h-screen flex flex-col bg-zinc-50 dark:bg-black font-sans">
      {/* Top Bar with user info and Logout */}
      <header className="border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 px-6 py-4 flex justify-between items-center">
        <Link href="/" className="flex items-center gap-2 font-bold text-lg text-zinc-900 dark:text-zinc-50">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-900 text-white dark:bg-zinc-50 dark:text-zinc-900">
            <Building2 className="h-5 w-5" />
          </div>
          <span>SocietySync</span>
        </Link>

        <div className="flex items-center gap-4 text-sm">
          <span className="text-zinc-600 dark:text-zinc-400">
            Signed in as <strong className="text-zinc-900 dark:text-zinc-100">{user?.first_name} {user?.last_name}</strong>
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              logout();
              router.replace('/login');
            }}
            className="flex items-center gap-1.5"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span>Sign Out</span>
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex justify-center items-center px-4 py-12">
        <div className="w-full max-w-xl">
          <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 shadow-sm">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl font-bold">Find & Join Your Society</CardTitle>
              <CardDescription>
                Select the residential complex where your flat is located to request membership.
              </CardDescription>
            </CardHeader>

            <CardContent>
              {error && (
                <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <form onSubmit={handleJoin} className="space-y-5">
                {/* Search Input */}
                <div className="space-y-1.5">
                  <Label htmlFor="search">Search Society</Label>
                  <div className="relative">
                    <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-400" />
                    <Input
                      id="search"
                      type="text"
                      placeholder="Type society name, city, or area..."
                      className="pl-9"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                  </div>
                </div>

                {/* Society List */}
                <div className="space-y-1.5">
                  <Label>Available Societies</Label>
                  {loading ? (
                    <div className="flex justify-center items-center py-10 border border-dashed rounded-lg border-zinc-200 dark:border-zinc-800">
                      <Loader2 className="h-6 w-6 animate-spin text-zinc-400 mr-2" />
                      <span className="text-sm text-zinc-500">Loading societies...</span>
                    </div>
                  ) : filteredSocieties.length === 0 ? (
                    <div className="text-center py-8 border border-dashed rounded-lg border-zinc-200 dark:border-zinc-800 text-zinc-500 text-sm">
                      {societies.length === 0
                        ? 'No societies are currently registered in the system.'
                        : 'No societies match your search query.'}
                    </div>
                  ) : (
                    <div className="max-h-56 overflow-y-auto space-y-2 pr-1">
                      {filteredSocieties.map((s) => {
                        const isSelected = selectedSocietyId === s.id;
                        return (
                          <div
                            key={s.id}
                            onClick={() => setSelectedSocietyId(s.id)}
                            className={`p-3 rounded-lg border cursor-pointer transition-all flex items-start justify-between ${
                              isSelected
                                ? 'border-zinc-900 bg-zinc-50 dark:border-zinc-100 dark:bg-zinc-900'
                                : 'border-zinc-200 dark:border-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-700'
                            }`}
                          >
                            <div className="space-y-0.5">
                              <p className="font-semibold text-zinc-900 dark:text-zinc-100 text-sm">
                                {s.name}
                              </p>
                              <div className="flex items-center gap-1 text-xs text-zinc-500">
                                <MapPin className="h-3 w-3 shrink-0" />
                                <span>{s.city}, {s.state}</span>
                              </div>
                              {s.address && (
                                <p className="text-xs text-zinc-400 line-clamp-1">{s.address}</p>
                              )}
                            </div>
                            {isSelected && (
                              <CheckCircle className="h-4 w-4 text-zinc-900 dark:text-zinc-100 mt-1 shrink-0" />
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Residency Type / Role */}
                <div className="space-y-1.5">
                  <Label>Your Residency Type</Label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => setRole('resident')}
                      className={`p-3 rounded-lg border text-left text-sm transition-all ${
                        role === 'resident'
                          ? 'border-zinc-900 bg-zinc-50 dark:border-zinc-100 dark:bg-zinc-900 font-medium'
                          : 'border-zinc-200 dark:border-zinc-800 hover:border-zinc-300'
                      }`}
                    >
                      <span className="block font-semibold">Flat Owner</span>
                      <span className="text-xs text-zinc-500">I own a flat in this society</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setRole('tenant')}
                      className={`p-3 rounded-lg border text-left text-sm transition-all ${
                        role === 'tenant'
                          ? 'border-zinc-900 bg-zinc-50 dark:border-zinc-100 dark:bg-zinc-900 font-medium'
                          : 'border-zinc-200 dark:border-zinc-800 hover:border-zinc-300'
                      }`}
                    >
                      <span className="block font-semibold">Tenant</span>
                      <span className="text-xs text-zinc-500">I am renting a flat here</span>
                    </button>
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={!selectedSocietyId || submitting}
                  className="w-full h-10 mt-2"
                >
                  {submitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  {submitting ? 'Submitting Request...' : 'Submit Join Request'}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}

export default function JoinSocietyPage() {
  return (
    <AuthGuard>
      <JoinSocietyContent />
    </AuthGuard>
  );
}
