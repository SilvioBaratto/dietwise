import { Component, ChangeDetectionStrategy, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideAlertTriangle, LucideCircleX, LucideX } from '@lucide/angular';
import { LlmErrorService } from '../../services/llm-error.service';

@Component({
  selector: 'app-llm-error-toast',
  imports: [RouterLink, LucideAlertTriangle, LucideCircleX, LucideX],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (error()) {
      <div class="fixed top-4 right-4 z-[9999] max-w-sm w-full shadow-lg rounded-xl border p-4
                  {{ isRateLimit() ? 'bg-amber-50 border-amber-300' : 'bg-red-50 border-red-300' }}">
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0 mt-0.5">
            @if (isRateLimit()) {
              <svg lucideAlertTriangle aria-hidden="true" class="w-5 h-5 text-amber-500"></svg>
            } @else {
              <svg lucideCircleX aria-hidden="true" class="w-5 h-5 text-red-500"></svg>
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
                  aria-label="Chiudi"
                  (click)="dismiss()">
            <svg lucideX aria-hidden="true" class="w-4 h-4"></svg>
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
