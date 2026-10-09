export type UserRole = 
    | 'platform_admin'
    | 'society_admin'
    | 'committee'
    | 'resident'
    | 'security_guard'
    | 'member'

export type UserAccountStatus =                                                                                                                                                           
   | 'registered'                                                                                                                                                                          
   | 'email_verified'                                                                                                                                                                      
   | 'activation_pending'                                                                                                                                                                  
   | 'active'                                                                                                                                                                              
   | 'suspended';                                                                                                                                                                          
                                                                                                                                                                                              
export type MembershipStatus =                                                                                                                                                            
  | 'unlinked'                                                                                                                                                                            
  | 'pending'                                                                                                                                                                             
  | 'approved'                                                                                                                                                                            
  | 'rejected';    


export interface User {
    user_id: string;
    first_name: string;
    last_name: string;
    email: string;
    role: UserRole;
    status: UserAccountStatus;
    email_verified: boolean;
    active_society_id: string | null;
    society_role: UserRole | string | null;
    membership_status: MembershipStatus;
    unit_id?: string | null;
    unit_number?: string | null;
}
export interface AuthTokens {
      access_token: string;
      token_type: 'bearer';
    }
  
export interface LoginResponseData {
  access_token: string;
  user: User;
}
  
export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data: T;
}