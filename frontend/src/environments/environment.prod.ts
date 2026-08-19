import type { AppEnvironment } from './environment.model';

export const environment: AppEnvironment = {
    production: true,
    // Use relative URL - Vercel will proxy /api/* to the backend via vercel.json rewrites
    // This hides the actual backend URL from users
    apiUrl: '/api/v1',
    supabaseUrl: '',
    supabaseAnonKey: '',
    devUserId: null
} 