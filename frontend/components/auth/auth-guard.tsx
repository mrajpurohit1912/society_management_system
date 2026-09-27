'use client';                                                                                                                                                                             
                                                                                                                                                                                              
    import { useEffect, useSyncExternalStore } from 'react';                                                                                                                                  
    import { useRouter, usePathname } from 'next/navigation';                                                                                                                                 
    import { useAuthStore } from '@/lib/store/auth-store';                                                                                                                                    
    import { UserRole } from '@/types/auth';                                                                                                                                                  
    import { Loader2 } from 'lucide-react';                                                                                                                                                   
                                                                                                                                                                                              
    interface AuthGuardProps {                                                                                                                                                                
      children: React.ReactNode;                                                                                                                                                              
      allowedRoles?: UserRole[];                                                                                                                                                              
    }                                                                                                                                                                                         
                                                                                                                                                                                              
    // React 19 recommended hydration subscriber                                                                                                                                              
    const emptySubscribe = () => () => {};                                                                                                                                                    
                                                                                                                                                                                              
    export function AuthGuard({ children, allowedRoles }: AuthGuardProps) {                                                                                                                   
      const router = useRouter();                                                                                                                                                             
      const pathname = usePathname();                                                                                                                                                         
      const { user, isAuthenticated } = useAuthStore();                                                                                                                                       
                                                                                                                                                                                              
      // Official React 19 hydration check (returns false on server, true on client mount)                                                                                                    
      const isHydrated = useSyncExternalStore(                                                                                                                                                
        emptySubscribe,                                                                                                                                                                       
        () => true,                                                                                                                                                                           
        () => false                                                                                                                                                                           
      );                                                                                                                                                                                      
                                                                                                                                                                                              
      useEffect(() => {                                                                                                                                                                       
        if (!isHydrated) return;                                                                                                                                                              
                                                                                                                                                                                              
        // 1. Not Authenticated -> Redirect to Login                                                                                                                                          
        if (!isAuthenticated || !user) {                                                                                                                                                      
          router.replace(`/login?redirect=${encodeURIComponent(pathname)}`);                                                                                                                  
          return;                                                                                                                                                                             
        }                                                                                                                                                                                     
                                                                                                                                                                                              
        // 2. Role Check: If user does not possess an allowed role -> Redirect                                                                                                                
        if (allowedRoles && allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {                                                                                                   
          if (user.role === 'platform_admin') {                                                                                                                                               
            router.replace('/platform/dashboard');                                                                                                                                            
          } else if (user.society_role === 'society_admin' && user.membership_status === 'approved') {                                                                                        
            router.replace('/admin/dashboard');                                                                                                                                               
          } else if (user.membership_status === 'approved') {                                                                                                                                 
            router.replace('/resident/dashboard');                                                                                                                                            
          } else {                                                                                                                                                                            
            router.replace('/onboarding/join-society');                                                                                                                                       
          }                                                                                                                                                                                   
          return;
        }
  
        // 3. Tenant Membership Check for non-platform users
        if (user.role !== 'platform_admin') {
          const isOnboardingRoute = pathname.startsWith('/onboarding');
  
          if (user.membership_status === 'unlinked' && pathname !== '/onboarding/join-society') {
            router.replace('/onboarding/join-society');
          } else if (user.membership_status === 'pending' && pathname !== '/onboarding/pending-approval') {
            router.replace('/onboarding/pending-approval');
          } else if (user.membership_status === 'approved' && isOnboardingRoute) {
            router.replace(user.society_role === 'society_admin' ? '/admin/dashboard' : '/resident/dashboard');
          }
        }
      }, [isHydrated, isAuthenticated, user, allowedRoles, router, pathname]);
  
      // Render centered spinner while checking authorization
      if (!isHydrated || !isAuthenticated || !user) {
        return (
          <div className="min-h-screen flex items-center justify-center bg-zinc-50 dark:bg-black">
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="h-8 w-8 animate-spin text-zinc-900 dark:text-zinc-50" />
              <p className="text-sm text-zinc-500 font-medium">Verifying authorization...</p>
            </div>
          </div>
        );
      }
  
      // Render protected content if all security checks pass
      return <>{children}</>;
    }