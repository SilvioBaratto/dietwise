import { Injectable } from '@angular/core';
import { Provider } from '../models/api-key.types';

const COST_ESTIMATES: Record<string, Record<string, string>> = {
  openai: {
    'gpt-5.4': '~$0.02-0.06',
    'gpt-5-mini': '~$0.005-0.02',
    'gpt-4.1': '~$0.01-0.03',
    'gpt-4.1-mini': '~$0.003-0.01',
    'gpt-4.1-nano': '~$0.001-0.005',
  },
  google: {
    'gemini-2.5-pro': '~$0.01-0.03',
    'gemini-2.5-flash': '~$0.003-0.01',
    'gemini-2.5-flash-lite': '~$0.001-0.005',
  },
  anthropic: {
    'claude-opus-4-6': '~$0.05-0.25',
    'claude-sonnet-4-6': '~$0.03-0.15',
    'claude-haiku-4-5': '~$0.01-0.05',
    'claude-sonnet-4-5': '~$0.03-0.15',
  },
};

@Injectable({ providedIn: 'root' })
export class CostEstimateService {
  getEstimate(provider: Provider, model: string): string | null {
    return COST_ESTIMATES[provider]?.[model] ?? null;
  }
}
