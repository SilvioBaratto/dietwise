import { Injectable, signal } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { LlmError, LlmErrorKind } from '../models/llm-error.types';

const ERROR_CODE_MAP: Record<string, LlmErrorKind> = {
  'API_KEY_NOT_CONFIGURED': 'KEY_NOT_CONFIGURED',
  'LLM_KEY_INVALID': 'KEY_INVALID',
  'LLM_QUOTA_EXCEEDED': 'QUOTA_EXCEEDED',
  'LLM_MODEL_UNAVAILABLE': 'MODEL_UNAVAILABLE',
  'RATE_LIMIT_ERROR': 'RATE_LIMITED',
  'LLM_PROVIDER_ERROR': 'PROVIDER_ERROR',
};

const LLM_ENDPOINT_PATTERNS = ['/diet', '/meals'];

@Injectable({ providedIn: 'root' })
export class LlmErrorService {
  private readonly _currentError = signal<LlmError | null>(null);
  readonly currentError = this._currentError.asReadonly();

  handleError(error: HttpErrorResponse): void {
    const url = error.url ?? '';
    if (!LLM_ENDPOINT_PATTERNS.some((p) => url.includes(p))) {
      return;
    }

    const code: string = error.error?.error?.code ?? '';
    const kind = ERROR_CODE_MAP[code];
    if (!kind) {
      return;
    }

    const message: string =
      error.error?.error?.message ?? 'An unexpected error occurred.';
    const provider: string | undefined =
      error.error?.error?.details?.provider;
    const retryAfterHeader = error.headers?.get('Retry-After');
    const retryAfter = retryAfterHeader ? parseInt(retryAfterHeader, 10) : undefined;

    this._currentError.set({ kind, message, provider, retryAfter });
  }

  dismiss(): void {
    this._currentError.set(null);
  }
}
