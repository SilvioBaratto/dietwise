import type { AppEnvironment } from './environment.model';

export const environment: AppEnvironment = {
    production: true,
    // Use relative URL - Vercel will proxy /api/* to the backend via vercel.json rewrites
    // This hides the actual backend URL from users
    apiUrl: '/api/v1',
    supabaseUrl: 'https://rbnimrabbjkmjrbflmxq.supabase.co',
    supabaseAnonKey: 'sb_publishable_nu8QYlWxIMt9lrgLmJYaCQ_wSfum6xv',
    devUserId: null
} 