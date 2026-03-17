// src/app/auth-callback/auth-callback.component.ts
import { Component, inject, ChangeDetectionStrategy, OnInit, DestroyRef } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '../services/auth.service';


// Global processing state to prevent duplicate processing across multiple component instances
const AUTH_PROCESSING_KEY = 'auth_callback_processing';

@Component({
    imports: [],
    changeDetection: ChangeDetectionStrategy.OnPush,
    template: `
        <div class="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-50 to-gray-100">
            <div class="text-center">
                <div class="w-16 h-16 border-4 border-teal-200 border-t-teal-600 rounded-full animate-spin mx-auto mb-4"></div>
                <p class="text-lg text-gray-700 font-medium">Autenticazione in corso...</p>
                <p class="text-sm text-gray-500 mt-2">Attendere prego</p>
            </div>
        </div>
    `,
})
export class AuthCallbackComponent implements OnInit {
    private readonly auth = inject(AuthService);
    private readonly router = inject(Router);
    private readonly route = inject(ActivatedRoute);
    private readonly destroyRef = inject(DestroyRef);

    ngOnInit() {
        // Process OAuth callback in ngOnInit
        this.processAuthCallback();
    }

    private async processAuthCallback() {
        // Check if already processing using sessionStorage (survives page refreshes)
        const processingTimestamp = sessionStorage.getItem(AUTH_PROCESSING_KEY);
        if (processingTimestamp) {
            const elapsedMs = Date.now() - parseInt(processingTimestamp, 10);
            // If less than 10 seconds have passed, skip processing
            if (elapsedMs < 10000) {
                console.log('[AuthCallback] Already processing, skipping duplicate call');
                return;
            }
            // If more than 10 seconds, allow retry (previous attempt may have failed)
            console.log('[AuthCallback] Previous processing timed out, retrying...');
        }

        // Mark as processing
        sessionStorage.setItem(AUTH_PROCESSING_KEY, Date.now().toString());

        // Clean up processing flag when component is destroyed
        this.destroyRef.onDestroy(() => {
            sessionStorage.removeItem(AUTH_PROCESSING_KEY);
        });

        console.log('[AuthCallback] Processing OAuth callback...');
        console.log('[AuthCallback] Current URL:', window.location.href);

        const returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/';

        try {
            // Check if there's a hash fragment with tokens
            const hashParams = new URLSearchParams(window.location.hash.substring(1));
            const hasTokenInHash = hashParams.has('access_token');

            // Check if there's a code parameter for PKCE flow
            const queryParams = this.route.snapshot.queryParams;
            const hasCode = !!queryParams['code'];

            console.log('[AuthCallback] Has token in hash:', hasTokenInHash);
            console.log('[AuthCallback] Has PKCE code:', hasCode);

            if (hasCode) {
                // PKCE flow
                console.log('[AuthCallback] Using PKCE flow');
                await this.auth.handleAuthCallbackPKCE();
            } else if (hasTokenInHash) {
                // Implicit flow (tokens in hash)
                console.log('[AuthCallback] Using implicit flow');
                await this.auth.handleAuthCallback();
            } else {
                // No tokens found - might be an error
                console.error('[AuthCallback] No tokens or code found in URL');
                const error = queryParams['error'];
                const errorDescription = queryParams['error_description'];

                if (error) {
                    console.error('[AuthCallback] OAuth error:', error, errorDescription);
                    throw new Error(errorDescription || error);
                }

                // Wait a bit for Supabase to process the URL
                await new Promise(resolve => setTimeout(resolve, 1000));

                // Try to get session one more time
                const session = await this.auth.getValidSession();
                if (!session) {
                    throw new Error('No session found after callback');
                }
            }

            console.log('[AuthCallback] Authentication successful, redirecting to:', returnUrl);

            // Clean up processing flag before redirect
            sessionStorage.removeItem(AUTH_PROCESSING_KEY);

            // Use replace to avoid back button issues
            await this.router.navigateByUrl(returnUrl, { replaceUrl: true });
        } catch (err) {
            console.error('[AuthCallback] Authentication failed:', err);

            // Clean up processing flag on error
            sessionStorage.removeItem(AUTH_PROCESSING_KEY);

            await this.router.navigate(['/login'], {
                queryParams: {
                    error: 'Authentication failed. Please try again.'
                },
                replaceUrl: true
            });
        }
    }
}
