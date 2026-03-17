// src/app/interceptors/auth.interceptor.ts
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, switchMap, throwError, from } from 'rxjs';
import { AuthService } from '../services/auth.service';
import { SupabaseService } from '../services/supabase.service';
import { environment } from '../../environments/environment';

/**
 * HTTP Interceptor that:
 * 1. Automatically adds Authorization header to all API requests
 * 2. Handles token refresh when token expires (401 errors)
 * 3. Retries failed requests after token refresh
 * 4. Redirects to pending-approval page on 403 (account not approved)
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const supabaseService = inject(SupabaseService);
  const router = inject(Router);

  // Check if this is an API request
  const isApiRequest = req.url.startsWith(environment.apiUrl) ||
                       req.url.startsWith('/api/');

  // Skip interceptor for non-API requests (e.g., external URLs, assets)
  if (!isApiRequest) {
    return next(req);
  }

  // Get current access token from session
  const session = authService.sessionSubject.value;
  const accessToken = session?.access_token;

  // If no token exists, proceed without auth header (user needs to sign in)
  if (!accessToken) {
    return next(req);
  }

  // Clone request and add Authorization header
  const authReq = req.clone({
    setHeaders: {
      Authorization: `Bearer ${accessToken}`
    }
  });

  // Execute request and handle errors
  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      // Handle 403 Forbidden - account pending approval
      if (error.status === 403) {
        const errorMessage = error.error?.error?.message || error.error?.message || '';
        if (errorMessage.toLowerCase().includes('pending approval') ||
            errorMessage.toLowerCase().includes('not approved')) {
          console.log('[AuthInterceptor] Account pending approval, redirecting...');
          router.navigate(['/pending-approval']);
          return throwError(() => error);
        }
      }

      // Handle 401 Unauthorized - token might be expired
      if (error.status === 401) {
        // Attempt to refresh the session using Supabase
        return from(refreshSession(supabaseService, authService)).pipe(
          switchMap((newSession) => {
            if (newSession?.access_token) {
              // Retry the original request with new token
              const retryReq = req.clone({
                setHeaders: {
                  Authorization: `Bearer ${newSession.access_token}`
                }
              });

              return next(retryReq);
            } else {
              // Refresh failed, throw original error
              return throwError(() => error);
            }
          }),
          catchError(() => {
            // If refresh fails, log user out and throw error
            authService.signOut();
            return throwError(() => error);
          })
        );
      }

      // For other errors, just pass them through
      return throwError(() => error);
    })
  );
};

/**
 * Helper function to refresh the Supabase session
 */
async function refreshSession(
  supabaseService: SupabaseService,
  authService: AuthService
) {
  try {
    // Supabase client automatically handles token refresh
    // when we call getSession() if autoRefreshToken is enabled
    const { data, error } = await supabaseService.client.auth.refreshSession();

    if (error) {
      throw error;
    }

    if (data.session) {
      // Update the auth service with new session
      authService.sessionSubject.next(data.session);
      return data.session;
    }

    return null;
  } catch (err) {
    throw err;
  }
}
