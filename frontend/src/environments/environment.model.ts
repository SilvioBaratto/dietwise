export interface AppEnvironment {
  production: boolean;
  apiUrl: string;
  supabaseUrl: string;
  supabaseAnonKey: string;

  /** Present only in dev builds */
  devUserId?: string | null;
}
