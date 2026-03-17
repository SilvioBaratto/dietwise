import { Component, ChangeDetectionStrategy, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LlmErrorService } from '../../services/llm-error.service';

@Component({
  selector: 'app-llm-error-toast',
  imports: [RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (error()) {
      <div class="fixed top-4 right-4 z-[9999] max-w-sm w-full shadow-lg rounded-xl border p-4
                  {{ isRateLimit() ? 'bg-amber-50 border-amber-300' : 'bg-red-50 border-red-300' }}">
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0 mt-0.5">
            @if (isRateLimit()) {
              <svg class="w-5 h-5 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 6a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 6zm0 9a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
              </svg>
            } @else {
              <svg class="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clip-rule="evenodd"/>
              </svg>
            }
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium {{ isRateLimit() ? 'text-amber-800' : 'text-red-800' }}">
              {{ error()!.message }}
            </p>
            @if (isRateLimit() && error()!.retryAfter) {
              <p class="mt-1 text-xs {{ 'text-amber-600' }}">
                Riprova tra {{ error()!.retryAfter }} secondi.
              </p>
            }
            @if (showSettingsLink()) {
              <a routerLink="/settings"
                 class="mt-2 inline-block text-sm font-medium underline
                        {{ isRateLimit() ? 'text-amber-700 hover:text-amber-900' : 'text-red-700 hover:text-red-900' }}"
                 (click)="dismiss()">
                Vai alle Impostazioni
              </a>
            }
          </div>
          <button type="button"
                  class="flex-shrink-0 rounded-md p-1.5
                         {{ isRateLimit() ? 'text-amber-500 hover:bg-amber-100' : 'text-red-500 hover:bg-red-100' }}"
                  (click)="dismiss()">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
            </svg>
          </button>
        </div>
      </div>
    }
  `,
})
export class LlmErrorToastComponent {
  private llmErrorService = inject(LlmErrorService);

  error = this.llmErrorService.currentError;

  isRateLimit = computed(() => this.error()?.kind === 'RATE_LIMITED');

  showSettingsLink = computed(() => {
    const kind = this.error()?.kind;
    return kind === 'KEY_INVALID' || kind === 'KEY_NOT_CONFIGURED' ||
           kind === 'QUOTA_EXCEEDED' || kind === 'MODEL_UNAVAILABLE';
  });

  dismiss(): void {
    this.llmErrorService.dismiss();
  }
}
