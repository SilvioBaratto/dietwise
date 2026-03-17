// src/app/services/settings.service.ts
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { environment } from '../../environments/environment';

interface UserSettingsOut {
  readonly id: string;
  readonly user_id: string;
  readonly weight?: number;
  readonly height?: number;
  readonly other_data?: string;
  readonly goals?: string;
  readonly created_at: string;
  readonly updated_at: string;
}

@Injectable({ providedIn: 'root' })
export class SettingsService {
  private readonly http = inject(HttpClient);

  /**
   * Check if user has settings configured.
   * Returns true if settings exist, false if 404 (no settings), throws on other errors.
   *
   * Note: Authorization header is automatically added by authInterceptor
   */
  hasSettings(): Observable<boolean> {
    return this.http
      .get<UserSettingsOut>(`${environment.apiUrl}/settings/get_user_settings`)
      .pipe(
        map(() => true),
        catchError((error) => {
          // 404 means no settings found - this is expected for new users
          if (error.status === 404) {
            return of(false);
          }
          // For other errors, rethrow
          throw error;
        })
      );
  }
}
