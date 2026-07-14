import {
  Component,
  ChangeDetectionStrategy,
  input,
  output,
  signal,
  viewChild,
  ElementRef,
  effect,
  DestroyRef,
  inject,
} from '@angular/core';
import { LucideX, LucideFileText, LucideLoader, LucideCheck } from '@lucide/angular';

@Component({
  selector: 'app-modify-diet-sheet',
  imports: [LucideX, LucideFileText, LucideLoader, LucideCheck],
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    '(document:keydown.escape)': 'onEscape()',
  },
  template: `
    @if (isOpen() || closing()) {
      <!-- Backdrop -->
      <div
        class="fixed inset-0 z-50 bg-black/30 animate-fade-in motion-reduce:animate-none"
        [class.is-closing]="closing()"
        (click)="close()"
        aria-hidden="true"
      ></div>

      <!-- Sheet -->
      <div
        #sheetEl
        class="fixed inset-x-0 bottom-0 z-50 mx-auto max-w-2xl bg-surface-raised rounded-t-xl shadow-2xl max-h-[85dvh] flex flex-col animate-slide-up motion-reduce:animate-none"
        [class.is-closing]="closing()"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modify-diet-sheet-title"
        (keydown)="onSheetKeydown($event)"
        (touchstart)="onTouchStart($event)"
        (touchmove)="onTouchMove($event)"
        (touchend)="onTouchEnd()"
      >
        <!-- Handle -->
        <div class="flex justify-center pt-3 pb-1 flex-shrink-0">
          <div class="w-10 h-1 rounded-full bg-border"></div>
        </div>

        <!-- Header -->
        <div class="flex items-center justify-between gap-3 px-5 sm:px-6 pb-3 flex-shrink-0">
          <div class="flex items-center gap-3 min-w-0">
            <svg lucideFileText aria-hidden="true" class="w-5 h-5 sm:w-6 sm:h-6 text-primary flex-shrink-0"></svg>
            <h2 id="modify-diet-sheet-title" class="text-base sm:text-lg font-display font-bold text-text truncate">
              Modifica Dieta
            </h2>
          </div>
          <button
            type="button"
            (click)="close()"
            [disabled]="modifying()"
            class="flex items-center justify-center min-h-11 min-w-11 -mr-2 rounded-full text-text-secondary hover:text-text hover:bg-surface-inset transition-colors flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Chiudi modifica dieta"
          >
            <svg lucideX class="w-5 h-5" aria-hidden="true"></svg>
          </button>
        </div>

        <!-- Body -->
        <div class="flex-1 overflow-y-auto overscroll-contain px-5 sm:px-6">
          <p class="text-sm sm:text-base text-text-secondary leading-relaxed mb-4">
            Descrivi cosa vuoi cambiare nella tua dieta. L'intelligenza artificiale modificherà solo gli aspetti
            richiesti mantenendo il resto invariato.
          </p>

          <div class="mb-4 p-4 bg-primary-light rounded-xl">
            <p class="text-sm font-semibold text-text mb-2">Esempi di richieste:</p>
            <ul class="text-sm text-text-secondary space-y-1 list-disc list-inside">
              <li>"Sostituisci la colazione di lunedì con qualcosa senza uova"</li>
              <li>"Voglio più proteine in tutte le cene"</li>
              <li>"Cambia tutti gli spuntini con frutta"</li>
              <li>"Rendi la dieta più mediterranea"</li>
            </ul>
          </div>

          <div class="space-y-2">
            <label for="modification-prompt" class="block text-sm font-semibold text-text">
              Cosa vuoi modificare?
            </label>
            <textarea
              #textareaEl
              id="modification-prompt"
              rows="4"
              [value]="prompt()"
              (input)="prompt.set($any($event.target).value)"
              placeholder="Es: Sostituisci la colazione di martedì con qualcosa senza latticini..."
              class="w-full px-4 py-3 text-base border border-border rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition-colors resize-none"
              [disabled]="modifying()"
            ></textarea>
          </div>

          @if (prompt().length > 0) {
            <p class="mt-2 text-sm text-text-secondary">{{ prompt().length }} caratteri</p>
          }
        </div>

        <!-- Footer -->
        <div class="px-5 sm:px-6 py-4 pb-safe border-t border-border flex-shrink-0">
          <div class="flex gap-3">
            <button
              type="button"
              (click)="close()"
              [disabled]="modifying()"
              class="flex-1 px-4 py-2.5 min-h-11 rounded-xl bg-surface-inset hover:bg-border text-text text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Annulla modifica"
            >
              Annulla
            </button>
            <button
              type="button"
              (click)="submit()"
              [disabled]="modifying() || prompt().trim().length === 0"
              class="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 min-h-11 rounded-xl bg-primary hover:bg-primary-hover text-white text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Conferma modifica dieta"
            >
              @if (modifying()) {
                <svg lucideLoader aria-hidden="true" class="w-4 h-4 animate-spin flex-shrink-0"></svg>
                <span>Modifica in corso...</span>
              } @else {
                <svg lucideCheck aria-hidden="true" class="w-4 h-4 flex-shrink-0"></svg>
                <span>Modifica</span>
              }
            </button>
          </div>
        </div>
      </div>
    }
  `,
  styles: `
    @media (prefers-reduced-motion: no-preference) {
      .animate-fade-in {
        animation: fade-in 0.2s ease-out both;
      }
      .animate-slide-up {
        animation: slide-up 0.3s cubic-bezier(0.32, 0.72, 0, 1) both;
      }

      @keyframes fade-in {
        from {
          opacity: 0;
        }
        to {
          opacity: 1;
        }
      }

      @keyframes slide-up {
        from {
          transform: translateY(100%);
        }
        to {
          transform: translateY(0);
        }
      }

      /* Exit animations — mirror the open, played while .is-closing is set */
      .animate-fade-in.is-closing {
        animation: fade-in 0.2s ease reverse forwards;
      }
      .animate-slide-up.is-closing {
        animation: slide-down 0.24s ease-in forwards;
      }
      @keyframes slide-down {
        from {
          transform: translateY(0);
        }
        to {
          transform: translateY(100%);
        }
      }
    }
  `,
})
export class ModifyDietSheetComponent {
  private readonly destroyRef = inject(DestroyRef);
  private readonly sheetElRef = viewChild<ElementRef<HTMLElement>>('sheetEl');
  private readonly textareaRef = viewChild<ElementRef<HTMLTextAreaElement>>('textareaEl');

  readonly isOpen = input<boolean>(false);
  readonly modifying = input<boolean>(false);
  readonly closed = output<void>();
  readonly submitted = output<string>();

  /** True while the sheet plays its exit animation before unmounting. */
  readonly closing = signal(false);
  readonly prompt = signal('');
  private closeTimer?: ReturnType<typeof setTimeout>;

  private touchStartY = 0;
  private touchDeltaY = 0;
  private previousOverflow = '';

  constructor() {
    effect(() => {
      if (this.isOpen()) {
        if (this.closeTimer) {
          clearTimeout(this.closeTimer);
          this.closeTimer = undefined;
        }
        this.closing.set(false);
        this.prompt.set('');
        this.lockScroll();
        setTimeout(() => this.textareaRef()?.nativeElement.focus(), 100);
      } else if (!this.closing()) {
        this.unlockScroll();
      }
    });

    this.destroyRef.onDestroy(() => {
      if (this.closeTimer) clearTimeout(this.closeTimer);
      this.unlockScroll();
    });
  }

  close() {
    if (this.closing() || this.modifying()) return;
    const reduce =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce) {
      this.closed.emit();
      return;
    }
    // Play the exit animation, then tell the parent to unmount us.
    this.closing.set(true);
    this.closeTimer = setTimeout(() => {
      this.closing.set(false);
      this.closeTimer = undefined;
      this.closed.emit();
    }, 250);
  }

  submit() {
    const trimmed = this.prompt().trim();
    if (!trimmed || this.modifying()) return;
    this.submitted.emit(trimmed);
  }

  onEscape() {
    if (this.isOpen() && !this.modifying()) this.close();
  }

  /** Focus trap — keep Tab/Shift+Tab inside the sheet */
  onSheetKeydown(event: KeyboardEvent) {
    if (event.key !== 'Tab') return;

    const sheetEl = this.sheetElRef()?.nativeElement;
    if (!sheetEl) return;

    const focusable = sheetEl.querySelectorAll<HTMLElement>(
      'button:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
    );
    if (focusable.length === 0) return;

    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  onTouchStart(event: TouchEvent) {
    this.touchStartY = event.touches[0].clientY;
    this.touchDeltaY = 0;
  }

  onTouchMove(event: TouchEvent) {
    this.touchDeltaY = event.touches[0].clientY - this.touchStartY;
  }

  onTouchEnd() {
    if (this.touchDeltaY > 80 && !this.modifying()) {
      this.close();
    }
  }

  private lockScroll() {
    if (typeof document !== 'undefined') {
      this.previousOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
    }
  }

  private unlockScroll() {
    if (typeof document !== 'undefined') {
      document.body.style.overflow = this.previousOverflow;
    }
  }
}
