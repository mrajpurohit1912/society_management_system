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
    if (error.response?.status === 401 && typeof window !== 'undefined') {                                                                                                         
        localStorage.removeItem('access_token');                                                                                                              
        if (window.location.pathname !== '/login') {                                                                                                                               
            window.location.href = '/login';                                                                                                                                       
        }                                                                                                                                                                          
    }     
        return Promise.reject(error);
    }
);