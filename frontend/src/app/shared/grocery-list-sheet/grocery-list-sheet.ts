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
import { ListaSpesa, Ingrediente } from '../../models/diet.types';
import { LucideX, LucideShoppingCart } from '@lucide/angular';

@Component({
  selector: 'app-grocery-list-sheet',
  imports: [LucideX, LucideShoppingCart],
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
        class="fixed inset-x-0 bottom-0 z-50 mx-auto max-w-2xl bg-surface-raised rounded-t-2xl shadow-2xl max-h-[85dvh] flex flex-col animate-slide-up motion-reduce:animate-none"
        [class.is-closing]="closing()"
        role="dialog"
        aria-modal="true"
        aria-labelledby="grocery-sheet-title"
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
            <svg lucideShoppingCart aria-hidden="true" class="w-5 h-5 sm:w-6 sm:h-6 text-primary flex-shrink-0"></svg>
            <h2 id="grocery-sheet-title" class="text-base sm:text-lg font-display font-bold text-text truncate">
              Lista della Spesa
            </h2>
          </div>
          <button
            #closeBtn
            type="button"
            (click)="close()"
            class="flex items-center justify-center min-h-11 min-w-11 -mr-2 rounded-full text-text-secondary hover:text-text hover:bg-surface-inset transition-colors flex-shrink-0"
            aria-label="Chiudi lista della spesa"
          >
            <svg lucideX class="w-5 h-5" aria-hidden="true"></svg>
          </button>
        </div>

        <!-- Ingredients list -->
        <div class="flex-1 overflow-y-auto overscroll-contain px-5 sm:px-6 pb-safe">
          @if (groceryList(); as list) {
            <div class="space-y-2 pb-4">
              @for (ingrediente of list.ingredienti; track trackByNome($index, ingrediente)) {
                <div
                  class="flex items-center justify-between gap-3 px-4 py-3 bg-surface-inset rounded-xl min-h-[52px]"
                >
                  <div class="flex items-center gap-3 flex-1 min-w-0">
                    <span class="w-2 h-2 rounded-full bg-primary flex-shrink-0" aria-hidden="true"></span>
                    <span class="font-medium text-text text-sm sm:text-base line-clamp-2">{{ ingrediente.nome }}</span>
                  </div>
                  <div class="flex items-baseline gap-1 flex-shrink-0">
                    <span class="text-base sm:text-lg font-bold text-text">{{ ingrediente.quantita }}</span>
                    <span class="text-xs sm:text-sm text-text-secondary font-medium">{{ ingrediente.unita }}</span>
                  </div>
                </div>
              }
            </div>
            <div class="pb-6 pt-2 border-t border-border">
              <p class="text-sm text-text-secondary text-center pt-3">
                Totale: <span class="font-semibold text-primary">{{ list.ingredienti.length }}</span> ingredienti
              </p>
            </div>
          }
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
export class GroceryListSheetComponent {
  private readonly destroyRef = inject(DestroyRef);
  private readonly sheetElRef = viewChild<ElementRef<HTMLElement>>('sheetEl');
  private readonly closeBtnRef = viewChild<ElementRef<HTMLButtonElement>>('closeBtn');

  readonly isOpen = input<boolean>(false);
  readonly groceryList = input<ListaSpesa | null>(null);
  readonly closed = output<void>();

  /** True while the sheet plays its exit animation before unmounting. */
  readonly closing = signal(false);
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
        this.lockScroll();
        setTimeout(() => this.closeBtnRef()?.nativeElement.focus(), 100);
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
    if (this.closing()) return;
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

  onEscape() {
    if (this.isOpen()) this.close();
  }

  trackByNome(_index: number, ingrediente: Ingrediente): string {
    return ingrediente.nome;
  }

  /** Focus trap — keep Tab/Shift+Tab inside the sheet */
  onSheetKeydown(event: KeyboardEvent) {
    if (event.key !== 'Tab') return;

    const sheetEl = this.sheetElRef()?.nativeElement;
    if (!sheetEl) return;

    const focusable = sheetEl.querySelectorAll<HTMLElement>(
      'button:not([disabled]), [tabindex]:not([tabindex="-1"])',
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
    if (this.touchDeltaY > 80) {
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
