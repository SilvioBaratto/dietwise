import { Injectable } from '@angular/core';
import { Provider } from '../models/api-key.types';

const COST_ESTIMATES: Record<string, Record<string, string>> = {
  openai: {
    'gpt-4o': '~$0.02-0.05',
    'gpt-4o-mini': '~$0.005-0.01',
    'gpt-4-turbo': '~$0.03-0.08',
    'gpt-3.5-turbo': '~$0.002-0.005',
  },
  google: {
    'gemini-2.0-flash': '~$0.005-0.01',
    'gemini-1.5-pro': '~$0.01-0.03',
    'gemini-1.5-flash': '~$0.003-0.008',
  },
  anthropic: {
    'claude-opus-4-5': '~$0.10-0.25',
    'claude-sonnet-4-5': '~$0.03-0.08',
    'claude-3-haiku-20240307': '~$0.002-0.005',
  },
};

@Injectable({ providedIn: 'root' })
export class CostEstimateService {
  getEstimate(provider: Provider, model: string): string | null {
    return COST_ESTIMATES[provider]?.[model] ?? null;
  }
}
