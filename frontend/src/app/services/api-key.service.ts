// src/app/services/api-key.service.ts

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  ApiKeyResponse,
  Preferences,
  Provider,
  ProvidersResponse,
  SaveKeyOptions,
  ValidateKeyResponse,
} from '../models/api-key.types';

@Injectable({ providedIn: 'root' })
export class ApiKeyService {
  private readonly http = inject(HttpClient);

  getKeys(): Observable<ApiKeyResponse[]> {
    return this.http.get<ApiKeyResponse[]>(`${environment.apiUrl}/api-keys`);
  }

  saveKey(
    provider: Provider,
    apiKey: string,
    options?: SaveKeyOptions,
  ): Observable<ApiKeyResponse> {
    return this.http.post<ApiKeyResponse>(`${environment.apiUrl}/api-keys`, {
      provider,
      // An empty string fails the backend's min_length=10 check (it only
      // waives that check for null/omitted, i.e. Ollama's optional key).
      api_key: apiKey || null,
      ...(options?.baseUrl ? { base_url: options.baseUrl } : {}),
      ...(options?.apiVersion ? { api_version: options.apiVersion } : {}),
    });
  }

  deleteKey(provider: Provider): Observable<void> {
    return this.http.delete<void>(`${environment.apiUrl}/api-keys/${provider}`);
  }

  validateKey(
    provider: Provider,
    apiKey: string,
    options?: SaveKeyOptions,
  ): Observable<ValidateKeyResponse> {
    return this.http.post<ValidateKeyResponse>(`${environment.apiUrl}/api-keys/validate`, {
      provider,
      api_key: apiKey || null,
      ...(options?.baseUrl ? { base_url: options.baseUrl } : {}),
      ...(options?.apiVersion ? { api_version: options.apiVersion } : {}),
    });
  }

  getProviders(): Observable<ProvidersResponse> {
    return this.http.get<ProvidersResponse>(`${environment.apiUrl}/api-keys/providers`);
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
