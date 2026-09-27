import {create} from 'zustand';
import {persist,createJSONStorage} from 'zustand/middleware';
import { User, MembershipStatus, UserRole } from '@/types/auth';     


interface AuthState {                                                                                                                                                                     
     token: string | null;                                                                                                                                                                   
     user: User | null;                                                                                                                                                                      
     isAuthenticated: boolean;                                                                                                                                                               
     login: (token: string, user: User) => void;                                                                                                                                             
     logout: () => void;                                                                                                                                                                     
     updateUser: (partialUser: Partial<User>) => void;                                                                                                                                       
     setMembership: (                                                                                                                                                                        
       societyId: string | null,                                                                                                                                                             
       role: UserRole | string,                                                                                                                                                              
       status: MembershipStatus                                                                                                                                                              
     ) => void;                                                                                                                                                                              
   }   
    export const useAuthStore = create<AuthState>()(                                                                                                                                          
      persist(                                                                                                                                                                                
        (set) => ({                                                                                                                                                                           
          token: null,                                                                                                                                                                        
          user: null,                                                                                                                                                                         
          isAuthenticated: false,                                                                                                                                                             
                                                                                                                                                                                              
          login: (token: string, user: User) => {                                                                                                                                             
            if (typeof window !== 'undefined') {                                                                                                                                              
              localStorage.setItem('access_token', token);                                                                                                                                    
            }                                                                                                                                                                                 
            set({                                                                                                                                                                             
              token,                                                                                                                                                                          
              user,                                                                                                                                                                           
              isAuthenticated: true,                                                                                                                                                          
            });                                                                                                                                                                               
          },                                                                                                                                                                                  
                                                                                                                                                                                              
          logout: () => {                                                                                                                                                                     
            if (typeof window !== 'undefined') {                                                                                                                                              
              localStorage.removeItem('access_token');                                                                                                                                        
            }                                                                                                                                                                                 
            set({                                                                                                                                                                             
              token: null,                                                                                                                                                                    
              user: null,                                                                                                                                                                     
              isAuthenticated: false,                                                                                                                                                         
            });                                                                                                                                                                               
          },                                                                                                                                                                                  
                                                                                                                                                                                              
          updateUser: (partialUser: Partial<User>) =>                                                                                                                                         
            set((state) => ({                                                                                                                                                                 
              user: state.user ? { ...state.user, ...partialUser } : null,                                                                                                                    
            })),                                                                                                                                                                              
                                                                                                                                                                                              
          setMembership: (                                                                                                                                                                    
            societyId: string | null,                                                                                                                                                         
            role: UserRole | string,                                                                                                                                                          
            status: MembershipStatus                                                                                                                                                          
          ) =>                                                                                                                                                                                
            set((state) => ({                                                                                                                                                                 
              user: state.user                                                                                                                                                                
                ? {
                    ...state.user,
                    active_society_id: societyId,
                    society_role: role,
                    membership_status: status,
                  }
                : null,
            })),
        }),
        {
          name: 'society-auth-storage',
          storage: createJSONStorage(() => localStorage),
        }
      )
    );