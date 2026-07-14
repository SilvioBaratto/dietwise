// src/app/services/user.service.ts
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

interface AcceptTermsResponse {
  readonly terms_accepted_at: string;
}

@Injectable({ providedIn: 'root' })
export class UserService {
  private readonly http = inject(HttpClient);

  /**
   * Record that the current user has accepted the Terms & Conditions.
   * Note: Authorization header is automatically added by authInterceptor
   */
  acceptTerms(): Observable<AcceptTermsResponse> {
    return this.http.post<AcceptTermsResponse>(`${environment.apiUrl}/users/accept-terms`, {});
  }
}
