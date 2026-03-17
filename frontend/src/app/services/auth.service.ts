// src/app/services/auth.service.ts
import { Injectable, inject } from '@angular/core';
import { SupabaseService } from './supabase.service';
import { BehaviorSubject, Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import type { Session, User } from '@supabase/supabase-js';
import { environment } from '../../environments/environment';
import { Router } from '@angular/router';

@Injectable({ providedIn: 'root' })
export class AuthService {
    private readonly supabase = inject(SupabaseService);
    private readonly router = inject(Router);

    public readonly sessionSubject = new BehaviorSubject<Session | null>(null);
    readonly session$: Observable<Session | null> = this.sessionSubject.asObservable();
    readonly isAuthenticated$: Observable<boolean> = this.session$.pipe(map(s => !!s));
    readonly user$: Observable<User | null> = this.session$.pipe(map(s => s?.user ?? null));

    constructor() {
        // Always initialize real Supabase session
        this.initializeSession();
    }

    /**
     * Initialize session and set up auth state listener
     * Handles TOKEN_REFRESHED, SIGNED_IN, SIGNED_OUT events
     */
    private async initializeSession(): Promise<void> {
        try {
            // Get initial session - Supabase will auto-refresh if expired
            const session = await this.supabase.getSession();
            this.sessionSubject.next(session);

            // Listen to all auth state changes
            this.supabase.onAuthStateChange((event, session) => {
                console.log('[AuthService] Auth event:', event, 'Session:', session ? 'present' : 'null');

                switch (event) {
                    case 'INITIAL_SESSION':
                        // Session loaded from storage
                        this.sessionSubject.next(session);
                        break;

                    case 'SIGNED_IN':
                        // User signed in successfully
                        console.log('[AuthService] User signed in');
                        this.sessionSubject.next(session);
                        break;

                    case 'SIGNED_OUT':
                        // User signed out or session expired
                        console.log('[AuthService] User signed out');
                        this.sessionSubject.next(null);
                        // Redirect to login
                        setTimeout(() => {
                            this.router.navigate(['/login']);
                        }, 0);
                        break;

                    case 'TOKEN_REFRESHED':
                        // Access token was refreshed
                        console.log('[AuthService] Token refreshed successfully');
                        this.sessionSubject.next(session);
                        break;

                    case 'USER_UPDATED':
                        // User metadata updated
                        console.log('[AuthService] User updated');
                        this.sessionSubject.next(session);
                        break;

                    default:
                        // Handle any other events
                        this.sessionSubject.next(session);
                }
            });
        } catch (error) {
            console.error('[AuthService] Error initializing session:', error);
            this.sessionSubject.next(null);
        }
    }

    /**
     * Check if current session is valid and not expired
     * Returns true if session exists and token is still valid
     */
    isSessionValid(): boolean {
        const session = this.sessionSubject.value;
        if (!session) {
            return false;
        }

        // Check if token is expired
        const expiresAt = session.expires_at;
        if (!expiresAt) {
            return false;
        }

        // Token expires_at is in Unix timestamp (seconds)
        const expirationTime = expiresAt * 1000; // Convert to milliseconds
        const now = Date.now();

        // Token is valid if it hasn't expired yet
        return expirationTime > now;
    }

    /**
     * Check if token is about to expire (within 60 seconds)
     * Useful for proactive refresh
     */
    isTokenExpiringSoon(): boolean {
        const session = this.sessionSubject.value;
        if (!session?.expires_at) {
            return false;
        }

        const expirationTime = session.expires_at * 1000;
        const now = Date.now();
        const sixtySeconds = 60 * 1000;

        return (expirationTime - now) < sixtySeconds;
    }

    /**
     * Manually refresh the session
     * Call this when you need to ensure you have a fresh token
     */
    async refreshSession(): Promise<Session | null> {
        try {
            console.log('[AuthService] Manually refreshing session...');
            const session = await this.supabase.refreshSession();

            if (session) {
                console.log('[AuthService] Session refreshed successfully');
                this.sessionSubject.next(session);
                return session;
            } else {
                console.warn('[AuthService] Session refresh returned null');
                return null;
            }
        } catch (error) {
            console.error('[AuthService] Error refreshing session:', error);
            // If refresh fails, clear session and redirect to login
            this.sessionSubject.next(null);
            this.router.navigate(['/login']);
            return null;
        }
    }

    /**
     * Get current valid session, refreshing if necessary
     * This is the recommended way to get session in guards/components
     */
    async getValidSession(): Promise<Session | null> {
        const currentSession = this.sessionSubject.value;

        // No session exists
        if (!currentSession) {
            return null;
        }

        // Session is valid and not expiring soon
        if (this.isSessionValid() && !this.isTokenExpiringSoon()) {
            return currentSession;
        }

        // Token is expired or expiring soon - refresh it
        console.log('[AuthService] Token expired or expiring soon, refreshing...');
        return await this.refreshSession();
    }

    getUserId(): string | null {
        return this.sessionSubject.value?.user.id ?? null;
    }

    /** Kick off the Google OAuth flow */
    signInWithGoogle(): Promise<void> {
        return this.supabase.signInWithGoogle();
    }

    /** Complete OAuth callback, store session */
    async handleAuthCallback(): Promise<Session> {
        const session = await this.supabase.handleAuthCallback();
        this.sessionSubject.next(session);
        return session!;
    }

    async handleAuthCallbackPKCE(): Promise<Session> {
        const session = await this.supabase.handleAuthCallbackPKCE();
        this.sessionSubject.next(session);
        return session!;
    }

    async signOut(): Promise<void> {
        await this.supabase.signOut();
        this.sessionSubject.next(null);
    }
}
