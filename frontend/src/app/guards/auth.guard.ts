// src/app/guard/auth.guard.ts
import { inject, Injectable } from '@angular/core';
import {
    CanActivate,
    Router,
    UrlTree,
    ActivatedRouteSnapshot,
    RouterStateSnapshot,
} from '@angular/router';
import { Location } from '@angular/common';
import { AuthService } from '../services/auth.service';

const URL_CLEANED_KEY = 'auth_url_cleaned';

@Injectable({ providedIn: 'root' })
export class AuthGuard implements CanActivate {
    private readonly auth = inject(AuthService);
    private readonly router = inject(Router);
    private readonly location = inject(Location);

    async canActivate(
        _route: ActivatedRouteSnapshot,
        state: RouterStateSnapshot
    ): Promise<boolean | UrlTree> {
        try {
            console.log('[AuthGuard] Checking authentication for:', state.url);

            // Check if we're coming from OAuth callback (tokens in URL)
            const hasTokensInUrl = window.location.hash.includes('access_token') ||
                                   window.location.search.includes('code=');

            // Check if we've already cleaned the URL in this session
            const urlCleaned = sessionStorage.getItem(URL_CLEANED_KEY);

            if (hasTokensInUrl && !urlCleaned) {
                console.log('[AuthGuard] Tokens detected in URL, waiting for session initialization...');
                // Wait for session to be processed (max 3 seconds)
                for (let i = 0; i < 30; i++) {
                    await new Promise(resolve => setTimeout(resolve, 100));
                    const session = await this.auth.getValidSession();
                    if (session) {
                        console.log('[AuthGuard] Session initialized from URL tokens');

                        // Mark URL as cleaned to prevent infinite loop
                        sessionStorage.setItem(URL_CLEANED_KEY, 'true');

                        // Clean URL without navigation using location.replaceState
                        const cleanPath = state.url.split('?')[0].split('#')[0];
                        console.log('[AuthGuard] Cleaning URL in-place:', cleanPath);
                        this.location.replaceState(cleanPath);

                        // Allow navigation to proceed
                        return true;
                    }
                }
                console.warn('[AuthGuard] Timeout waiting for session from URL tokens');
            }

            // Clear the cleaned flag if no tokens in URL (normal navigation)
            if (!hasTokensInUrl && urlCleaned) {
                sessionStorage.removeItem(URL_CLEANED_KEY);
            }

            // Wait for session to be ready (handles page refresh after login)
            let session = this.auth.sessionSubject.value;

            // If no session yet, wait briefly for Supabase to initialize from storage
            if (!session) {
                console.log('[AuthGuard] No session yet, waiting for initialization...');
                for (let i = 0; i < 20; i++) {
                    await new Promise(resolve => setTimeout(resolve, 100));
                    session = this.auth.sessionSubject.value;
                    if (session) {
                        console.log('[AuthGuard] Session loaded from storage');
                        break;
                    }
                }
            }

            if (session) {
                console.log('[AuthGuard] Authentication successful');
                return true;
            }

            // No valid session - redirect to login
            console.log('[AuthGuard] No valid session, redirecting to login');
            return this.router.createUrlTree(
                ['/login'],
                { queryParams: { returnUrl: state.url } }
            );
        } catch (error) {
            console.error('[AuthGuard] Error checking authentication:', error);
            return this.router.createUrlTree(
                ['/login'],
                { queryParams: { returnUrl: state.url } }
            );
        }
    }
}