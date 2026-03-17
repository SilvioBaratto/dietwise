// src/app/models/api-key.types.ts

export type Provider = 'openai' | 'google' | 'anthropic';

export interface ApiKeyResponse {
  readonly provider: Provider;
  readonly key_hint: string;
  readonly is_valid: boolean;
  readonly updated_at: string;
}

export interface AvailableModels {
  readonly openai: string[];
  readonly google: string[];
  readonly anthropic: string[];
}

export interface Preferences {
  readonly provider: string | null;
  readonly model: string | null;
}

export interface ValidateKeyResponse {
  readonly provider: string;
  readonly is_valid: boolean;
  readonly error: string | null;
}
