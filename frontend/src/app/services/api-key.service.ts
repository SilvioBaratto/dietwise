// src/app/services/api-key.service.ts

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  ApiKeyResponse,
  AvailableModels,
  Preferences,
  Provider,
  ValidateKeyResponse,
} from '../models/api-key.types';

@Injectable({ providedIn: 'root' })
export class ApiKeyService {
  private readonly http = inject(HttpClient);

  getKeys(): Observable<ApiKeyResponse[]> {
    return this.http.get<ApiKeyResponse[]>(`${environment.apiUrl}/api-keys`);
  }

  saveKey(provider: Provider, apiKey: string): Observable<ApiKeyResponse> {
    return this.http.post<ApiKeyResponse>(`${environment.apiUrl}/api-keys`, {
      provider,
      api_key: apiKey,
    });
  }

  deleteKey(provider: Provider): Observable<void> {
    return this.http.delete<void>(`${environment.apiUrl}/api-keys/${provider}`);
  }

  validateKey(provider: Provider, apiKey: string): Observable<ValidateKeyResponse> {
    return this.http.post<ValidateKeyResponse>(`${environment.apiUrl}/api-keys/validate`, {
      provider,
      api_key: apiKey,
    });
  }

  getAvailableModels(): Observable<AvailableModels> {
    return this.http.get<AvailableModels>(`${environment.apiUrl}/api-keys/available-models`);
  }

  getPreferences(): Observable<Preferences> {
    return this.http.get<Preferences>(`${environment.apiUrl}/api-keys/preferences`);
  }

  updatePreferences(provider: Provider, model: string): Observable<void> {
    return this.http.put<void>(`${environment.apiUrl}/api-keys/preferences`, {
      provider,
      model,
    });
  }
}
