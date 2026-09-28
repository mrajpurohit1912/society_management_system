                                                                                                                                                                                        
    'use client';                                                                                                                                                                       
                                                                                                                                                                                        
    import { useState, Suspense } from 'react';                                                                                                                                         
    import Link from 'next/link';                                                                                                                                                       
    import { useRouter, useSearchParams } from 'next/navigation';                                                                                                                       
    import { apiClient } from '@/lib/api-client';                                                                                                                                       
    import { useAuthStore } from '@/lib/store/auth-store';                                                                                                                              
    import { Button } from '@/components/ui/button';                                                                                                                                    
    import { Input } from '@/components/ui/input';                                                                                                                                      
    import { Label } from '@/components/ui/label';                                                                                                                                      
    import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';                                                                                   
    import { Building2, Loader2, AlertCircle } from 'lucide-react';                                                                                                                     
                                                                                                                                                                                        
    function LoginForm() {                                                                                                                                                              
      const router = useRouter();                                                                                                                                                       
      const searchParams = useSearchParams();                                                                                                                                           
      const redirectUrl = searchParams.get('redirect');                                                                                                                                 
                                                                                                                                                                                        
      const login = useAuthStore((state) => state.login);                                                                                                                               
                                                                                                                                                                                        
      const [email, setEmail] = useState('');                                                                                                                                           
      const [password, setPassword] = useState('');                                                                                                                                     
      const [loading, setLoading] = useState(false);                                                                                                                                    
      const [error, setError] = useState<string | null>(null);                                                                                                                          
                                                                                                                                                                                        
      const handleLogin = async (e: React.FormEvent) => {                                                                                                                               
        e.preventDefault();                                                                                                                                                             
        setLoading(true);                                                                                                                                                               
        setError(null);                                                                                                                                                                 
                                                                                                                                                                                        
        try {                                                                                                                                                                           
          const response = await apiClient.post('/auth/login', { email, password });                                                                                                    
          const { access_token, user } = response.data.data;                                                                                                                            
                                                                                                                                                                                        
          // 1. Store credentials in Zustand + localStorage                                                                                                                             
          login(access_token, user);                                                                                                                                                    
                                                                                                                                                                                        
          // 2. If user was redirected from a deep-link, honor it                                                                                                                       
          if (redirectUrl) {                                                                                                                                                            
            router.replace(redirectUrl);                                                                                                                                                
            return;                                                                                                                                                                     
          }                                                                                                                                                                             
                                                                                                                                                                                        
          // 3. Intelligent Enterprise Role & Membership Routing                                                                                                                        
          if (user.role === 'platform_admin') {                                                                                                                                         
            router.replace('/platform/dashboard');                                                                                                                                      
          } else if (user.society_role === 'society_admin' && user.membership_status === 'approved') {                                                                                  
            router.replace('/admin/dashboard');                                                                                                                                         
          } else if (user.membership_status === 'approved') {                                                                                                                           
            router.replace('/resident/dashboard');                                                                                                                                      
          } else if (user.membership_status === 'pending') {                                                                                                                            
            router.replace('/onboarding/pending-approval');                                                                                                                             
          } else {                                                                                                                                                                      
            // Unlinked resident -> route to society join wizard                                                                                                                        
            router.replace('/onboarding/join-society');                                                                                                                                 
          }                                                                                                                                                                             
        } catch (err: unknown) {                                                                                                                                                        
          if (err instanceof Error) {                                                                                                                                                   
            setError(err.message);                                                                                                                                                      
          } else {                                                                                                                                                                      
            setError('Invalid email or password. Please try again.');                                                                                                                   
          }                                                                                                                                                                             
        } finally {                                                                                                                                                                     
          setLoading(false);                                                                                                                                                            
        }                                                                                                                                                                               
      };                                                                                                                                                                                
                                                                                                                                                                                        
      return (                                                                                                                                                                          
        <Card className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 shadow-sm">                                                                              
          <CardHeader className="text-center">                                                                                                                                          
            <CardTitle className="text-2xl font-bold">Sign In to Your Portal</CardTitle>                                                                                                
            <CardDescription>Enter your email and password to access your society.</CardDescription>                                                                                    
          </CardHeader>                                                                                                                                                                 
                                                                                                                                                                                        
          <CardContent>                                                                                                                                                                 
            {error && (                                                                                                                                                                 
              <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">                                                        
                <AlertCircle className="h-4 w-4 shrink-0" />                                                                                                                            
                <span>{error}</span>                                                                                                                                                    
              </div>                                                                                                                                                                    
            )}                                                                                                                                                                          
                                                                                                                                                                                        
            <form onSubmit={handleLogin} className="space-y-4">                                                                                                                         
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
                                                                                                                                                                                        
              <div className="space-y-1.5">                                                                                                                                             
                <div className="flex justify-between items-center">                                                                                                                     
                  <Label htmlFor="password">Password</Label>                                                                                                                            
                </div>                                                                                                                                                                  
                <Input                                                                                                                                                                  
                  id="password"                                                                                                                                                         
                  type="password"                                                                                                                                                       
                  required                                                                                                                                                              
                  placeholder="••••••••"                                                                                                                                                
                  value={password}                                                                                                                                                      
                  onChange={(e) => setPassword(e.target.value)}                                                                                                                         
                />                                                                                                                                                                      
              </div>                                                                                                                                                                    
                                                                                                                                                                                        
              <Button type="submit" disabled={loading} className="w-full h-10 mt-2">                                                                                                    
                {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}                                                                                                    
                {loading ? 'Authenticating...' : 'Sign In'}                                                                                                                             
              </Button>                                                                                                                                                                 
            </form>                                                                                                                                                                     
                                                                                                                                                                                        
            <div className="mt-6 text-center text-sm text-zinc-500">                                                                                                                    
              Don&apos;t have an account yet?{' '}                                                                                                                                      
              <Link href="/signup" className="text-zinc-900 font-semibold underline dark:text-zinc-100">                                                                                
                Sign up as Resident                                                                                                                                                     
              </Link>                                                                                                                                                                   
            </div>                                                                                                                                                                      
          </CardContent>                                                                                                                                                                
        </Card>                                                                                                                                                                         
      );                                                                                                                                                                                
    }                                                                                                                                                                                   
                                                                                                                                                                                        
    export default function LoginPage() {                                                                                                                                               
      return (                                                                                                                                                                          
        <div className="min-h-screen flex flex-col justify-center items-center px-4 bg-zinc-50 dark:bg-black font-sans">                                                                
          <div className="w-full max-w-md">                                                                                                                                             
            <div className="flex justify-center mb-8">                                                                                                                                  
              <Link href="/" className="flex items-center gap-2 font-bold text-2xl text-zinc-900 dark:text-zinc-50">                                                                    
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-zinc-900 text-white dark:bg-zinc-50 dark:text-zinc-900">                                       
                  <Building2 className="h-6 w-6" />                                                                                                                                     
                </div>                                                                                                                                                                  
                <span>SocietySync</span>                                                                                                                                                
              </Link>                                                                                                                                                                   
            </div>                                                                                                                                                                      
                                                                                                                                                                                        
            {/* Suspense boundary required by Next.js for useSearchParams */}                                                                                                           
            <Suspense                                                                                                                                                                   
              fallback={                                                                                                                                                                
                <div className="flex justify-center py-12">                                                                                                                             
                  <Loader2 className="h-8 w-8 animate-spin text-zinc-500" />                                                                                                            
                </div>                                                                                                                                                                  
              }                                                                                                                                                                         
            >                                                                                                                                                                           
              <LoginForm />                                                                                                                                                             
            </Suspense>                                                                                                                                                                 
          </div>                                                                                                                                                                        
        </div>                                                                                                                                                                          
      );                                                                                                                                                                                
    }              