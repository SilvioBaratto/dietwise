// src/app/services/supabase.service.ts
import { Injectable } from '@angular/core'
import {
    createClient,
    SupabaseClient,
    Session,
    AuthChangeEvent,
    User,
} from '@supabase/supabase-js'
import { environment } from '../../environments/environment'

@Injectable({ providedIn: 'root' })
export class SupabaseService {
    private static instance: SupabaseClient | null = null;
    public readonly client: SupabaseClient

    constructor() {
        // Use singleton pattern to prevent multiple client instances
        if (SupabaseService.instance) {
            console.log('[SupabaseService] Using existing client instance');
            this.client = SupabaseService.instance;
            return;
        }

        console.log('[SupabaseService] Creating new Supabase client...');
        this.client = createClient(
            environment.supabaseUrl,
            environment.supabaseAnonKey,
            {
                auth: {
                    persistSession: true,
                    autoRefreshToken: true,
                    detectSessionInUrl: true,
                    // Use a custom storage key to avoid conflicts
                    storageKey: 'sb-auth-token',
                    // Use PKCE flow for better security
                    flowType: 'pkce'
                }
            }
        );

        // Store singleton instance
        SupabaseService.instance = this.client;

        // Log client initialization
        console.log('[SupabaseService] Client initialized with PKCE flow');
    }

    async signInWithGoogle(): Promise<void> {
        // Clear any existing session before starting new OAuth flow
        await this.client.auth.signOut();

        const { error } = await this.client.auth.signInWithOAuth({
            provider: 'google',
            options: {
                redirectTo: `${window.location.origin}/auth/callback`,
                skipBrowserRedirect: false
            }
        });
        if (error) throw error;
    }

    /**
     * 3) On your /auth/callback route/component, call this to process
     *    the URL callback and store the session in local storage.
     */
    async handleAuthCallback(): Promise<Session> {
        const { data: { session }, error } = await this.client.auth.getSession();
        if (error) throw error;
        return session!;
    }

    async handleAuthCallbackPKCE(): Promise<Session> {
        console.log('[SupabaseService] Starting PKCE callback handling...');

        // First check if we already have a valid session (code may have been consumed)
        const { data: existingSessionData } = await this.client.auth.getSession();
        if (existingSessionData.session) {
            console.log('[SupabaseService] Session already exists, skipping code exchange');
            return existingSessionData.session;
        }

        const url = new URL(window.location.href);
        const code = url.searchParams.get('code');

        if (!code) {
            throw new Error('No auth code in URL');
        }

        console.log('[SupabaseService] Exchanging code for session...');

        const { data, error } = await this.client.auth.exchangeCodeForSession(code);

        if (error) {
            console.error('[SupabaseService] Code exchange error:', error.message);

            // If code was already consumed or verifier missing, try to get existing session
            if (error.message?.includes('code verifier') ||
                error.message?.includes('already been consumed') ||
                error.message?.includes('invalid request')) {
                console.log('[SupabaseService] Code already used, checking for existing session...');
                const { data: sessionData } = await this.client.auth.getSession();
                if (sessionData.session) {
                    console.log('[SupabaseService] Found existing valid session');
                    return sessionData.session;
                }
            }

            throw error;
        }

        console.log('[SupabaseService] Code exchange successful');
        return data.session!;
    }

    /** Get the current session (or null if not signed in) */
    async getSession(): Promise<Session | null> {
        const { data, error } = await this.client.auth.getSession()
        if (error) {
            console.error('Error getting session:', error)
            return null
        }
        return data.session
    }

    /**
     * Manually refresh the session using the refresh token
     * Returns a new session with fresh access_token and refresh_token
     */
    async refreshSession(): Promise<Session | null> {
        const { data, error } = await this.client.auth.refreshSession()
        if (error) {
            console.error('Error refreshing session:', error)
            return null
        }
        return data.session
    }

    /** Get the current user object */
    async getUser(): Promise<User | null> {
        const { data, error } = await this.client.auth.getUser()
        if (error) {
            console.error('Error getting user:', error)
            return null
        }
        return data.user
    }

    /** Sign out */
    async signOut(): Promise<void> {
        const { error } = await this.client.auth.signOut()
        if (error) console.error('Sign-out error:', error)
    }

    /**
     * Subscribe to auth state changes (e.g. SIGNED_IN, SIGNED_OUT)
     * Returns an unsubscribe function.
     */
    onAuthStateChange(
        callback: (event: AuthChangeEvent, session: Session | null) => void
    ): () => void {
        const { data } = this.client.auth.onAuthStateChange((event, session) => {
            callback(event, session)
        })
        return () => data.subscription.unsubscribe()
    }
}
