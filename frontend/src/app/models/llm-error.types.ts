export type LlmErrorKind =
  | 'KEY_INVALID'
  | 'KEY_NOT_CONFIGURED'
  | 'QUOTA_EXCEEDED'
  | 'MODEL_UNAVAILABLE'
  | 'RATE_LIMITED'
  | 'PROVIDER_ERROR';

export interface LlmError {
  kind: LlmErrorKind;
  message: string;
  provider?: string;
  retryAfter?: number;
}
