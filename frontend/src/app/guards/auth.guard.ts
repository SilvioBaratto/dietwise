// src/app/guards/auth.guard.ts
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { Location } from '@angular/common';
import { AuthService } from '../services/auth.service';

const URL_CLEANED_KEY = 'auth_url_cleaned';

export const authGuard: CanActivateFn = async (_route, state) => {
    const auth = inject(AuthService);
    const router = inject(Router);
    const location = inject(Location);

    try {
        console.log('[AuthGuard] Checking authentication for:', state.url);

        // Check if we're coming from OAuth callback (tokens in URL) - in this app,
        // the PKCE code sometimes lands directly on a guarded route instead of
        // /auth/callback, so this is load-bearing, not a leftover fallback.
        const hasTokensInUrl = window.location.hash.includes('access_token') ||
                               window.location.search.includes('code=');

        // Check if we've already cleaned the URL in this session
        const urlCleaned = sessionStorage.getItem(URL_CLEANED_KEY);

        if (hasTokensInUrl && !urlCleaned) {
            console.log('[AuthGuard] Tokens detected in URL, waiting for session initialization...');
            // Wait for session to be processed (max 3 seconds)
            for (let i = 0; i < 30; i++) {
                await new Promise(resolve => setTimeout(resolve, 100));
                const session = await auth.getValidSession();
                if (session) {
                    console.log('[AuthGuard] Session initialized from URL tokens');

                    // Mark URL as cleaned to prevent infinite loop
                    sessionStorage.setItem(URL_CLEANED_KEY, 'true');

                    // Clean URL without navigation using location.replaceState
                    const cleanPath = state.url.split('?')[0].split('#')[0];
                    console.log('[AuthGuard] Cleaning URL in-place:', cleanPath);
                    location.replaceState(cleanPath);

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

        // Wait for the initial session load (handles page refresh after login)
        await auth.waitUntilInitialized();

        if (auth.isAuthenticated()) {
            console.log('[AuthGuard] Authentication successful');
            return true;
        }

        // No valid session - redirect to login
        console.log('[AuthGuard] No valid session, redirecting to login');
        return router.createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
    } catch (error) {
        console.error('[AuthGuard] Error checking authentication:', error);
        return router.createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
    }
};

export const guestGuard: CanActivateFn = async () => {
    const auth = inject(AuthService);
    const router = inject(Router);

    await auth.waitUntilInitialized();

    if (!auth.isAuthenticated()) {
        return true;
    }

    return router.createUrlTree(['/']);
};
