// src/app/models/api-key.types.ts

export type Provider =
  | 'openai'
  | 'openai_responses'
  | 'anthropic'
  | 'google'
  | 'azure_openai'
  | 'openai_generic'
  | 'microsoft_foundry'
  | 'ollama';

export interface ApiKeyResponse {
  readonly provider: Provider;
  readonly key_hint: string;
  readonly is_valid: boolean;
  readonly updated_at: string;
  readonly base_url?: string | null;
  readonly api_version?: string | null;
}

export interface ProviderInfo {
  readonly slug: Provider;
  readonly label: string;
  readonly requires_api_key: boolean;
  readonly requires_base_url: boolean;
  readonly requires_api_version: boolean;
  readonly default_base_url: string | null;
  readonly free_form_models: boolean;
  readonly models: string[];
  readonly default_model: string | null;
  readonly key_format_hint: string | null;
}

export interface ProvidersResponse {
  readonly providers: ProviderInfo[];
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

export interface SaveKeyOptions {
  readonly baseUrl?: string;
  readonly apiVersion?: string;
}
