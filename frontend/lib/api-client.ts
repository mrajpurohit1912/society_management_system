import axios from 'axios';
import {v4 as uuidv4} from 'uuid';


export const apiClient = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1',
    headers: {
        'Content-Type':'application/json',
    },
    withCredentials:true,
});

apiClient.interceptors.request.use((config) => {
    config.headers['X-Correlation-ID'] = uuidv4();

    if (typeof window !== 'undefined') {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }      
    }
    return config;
});


apiClient.interceptors.response.use(                                                                                                                                                      
  (response) => response,                                                                                                                                                                 
  (error) => {                                                                                                                                                                            
    if (typeof window !== 'undefined') {
      // 1. Session Expiry / 401 Unauthorized Handling
      if (error.response?.status === 401) {           
        localStorage.removeItem('access_token');
        localStorage.removeItem('society-auth-storage');

        if (window.location.pathname !== '/login') {
          window.location.replace('/login');        
        }
      }   
       
      // 2. FastAPI Error Normalization (Formats Pydantic array into readable string)
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        if (Array.isArray(detail)) {
            const formattedError = detail.map((err: { msg: string }) => err.msg).join(', ');          
            return Promise.reject(new Error(formattedError));
        }
        if (typeof detail === 'string'){
          return Promise.reject(new Error(detail));
        }
      } 
      if (error.response?.data?.message) {
        return Promise.reject(new Error(error.response.data.message));
      }  
    }   
     
    return Promise.reject(error);
  }
);  