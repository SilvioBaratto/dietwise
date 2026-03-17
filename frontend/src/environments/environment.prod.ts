import type { AppEnvironment } from './environment.model';

export const environment: AppEnvironment = {
    production: true,
    // Use relative URL - Vercel will proxy /api/* to the backend via vercel.json rewrites
    // This hides the actual backend URL from users
    apiUrl: '/api/v1',
    supabaseUrl: 'https://rbnimrabbjkmjrbflmxq.supabase.co',
    supabaseAnonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJibmltcmFiYmprbWpyYmZsbXhxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTIwNTIyNTUsImV4cCI6MjA2NzYyODI1NX0.N9mWthlE530ooLYFir-5Bt7LHg0De8N6SAT2jg7Ldek',
    devUserId: null
} 