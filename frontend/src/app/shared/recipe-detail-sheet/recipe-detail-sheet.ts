import {
  Component,
  ChangeDetectionStrategy,
  input,
  output,
  signal,
  computed,
  viewChild,
  ElementRef,
  effect,
  DestroyRef,
  inject,
} from '@angular/core';
import { SavedRecipe } from '../../models/recipe.types';
import { LucideX, LucideFlame, LucideCalendar, LucideCopy } from '@lucide/angular';

interface RecipeSection {
  type: 'heading' | 'paragraph' | 'bullet' | 'numbered';
  content?: string;
  items?: string[];
}

const MEAL_TYPE_LABELS: Record<string, string> = {
  COLAZIONE: 'Colazione',
  SPUNTINO_MATTINA: 'Spuntino Mattina',
  PRANZO: 'Pranzo',
  SPUNTINO_POMERIGGIO: 'Spuntino Pomeriggio',
  CENA: 'Cena',
};

@Component({
  selector: 'app-recipe-detail-sheet',
  imports: [LucideX, LucideFlame, LucideCalendar, LucideCopy],
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
        aria-labelledby="recipe-sheet-title"
        (keydown)="onSheetKeydown($event)"
        (touchstart)="onTouchStart($event)"
        (touchmove)="onTouchMove($event)"
        (touchend)="onTouchEnd()"
      >
        <!-- Handle -->
        <div class="flex justify-center pt-3 pb-1 flex-shrink-0">
          <div class="w-10 h-1 rounded-full bg-border"></div>
        </div>

        @if (recipe(); as r) {
        <!-- Header -->
        <div class="flex items-start justify-between gap-3 px-5 sm:px-6 pb-3 flex-shrink-0">
          <div class="min-w-0">
            <h2 id="recipe-sheet-title" class="text-base sm:text-lg font-display font-bold text-text leading-tight">
              {{ r.recipe_name }}
            </h2>
            <div class="flex flex-wrap items-center gap-3 mt-2">
              <span class="text-xs font-bold uppercase tracking-wide text-primary">
                {{ mealTypeLabel(r.meal_type) }}
              </span>
              <div class="flex items-center gap-1.5 text-text-secondary">
                <svg lucideFlame aria-hidden="true" class="w-4 h-4 flex-shrink-0"></svg>
                <span class="text-xs font-medium">{{ r.calories }} kcal</span>
              </div>
              <div class="flex items-center gap-1.5 text-text-secondary">
                <svg lucideCalendar aria-hidden="true" class="w-4 h-4 flex-shrink-0"></svg>
                <span class="text-xs">{{ formatDate(r.created_at) }}</span>
              </div>
            </div>
          </div>
          <button
            #closeBtn
            type="button"
            (click)="close()"
            class="flex items-center justify-center min-h-11 min-w-11 -mr-2 -mt-1 rounded-full text-text-secondary hover:text-text hover:bg-surface-inset transition-colors flex-shrink-0"
            aria-label="Chiudi ricetta"
          >
            <svg lucideX class="w-5 h-5" aria-hidden="true"></svg>
          </button>
        </div>

        <!-- Recipe content -->
        <div class="flex-1 overflow-y-auto overscroll-contain px-5 sm:px-6 pb-safe">
          <div class="space-y-3 pb-4">
            @for (section of parsedSections(); track $index) {
              @switch (section.type) {
                @case ('heading') {
                  <h3 class="text-base font-bold text-text mt-3 first:mt-0">{{ section.content }}</h3>
                }
                @case ('paragraph') {
                  <p class="text-text-secondary text-sm leading-relaxed">{{ section.content }}</p>
                }
                @case ('bullet') {
                  <ul class="space-y-1.5">
                    @for (item of section.items; track $index) {
                      <li class="flex items-start gap-2 text-sm text-text-secondary leading-relaxed">
                        <span class="w-1.5 h-1.5 mt-2 bg-primary rounded-full flex-shrink-0" aria-hidden="true"></span>
                        <span>{{ item }}</span>
                      </li>
                    }
                  </ul>
                }
                @case ('numbered') {
                  <ol class="space-y-2">
                    @for (item of section.items; track $index; let idx = $index) {
                      <li class="flex items-start gap-2 text-sm text-text-secondary leading-relaxed">
                        <span class="flex-shrink-0 w-5 h-5 bg-primary-light text-primary font-bold rounded-full flex items-center justify-center text-xs" aria-hidden="true">{{ idx + 1 }}</span>
                        <span class="pt-0.5">{{ item }}</span>
                      </li>
                    }
                  </ol>
                }
              }
            }
          </div>

          <!-- Copy button -->
          <div class="pb-6 pt-2">
            <button type="button" (click)="copy()"
              class="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 min-h-11 rounded-xl bg-white border border-border hover:bg-surface-inset text-text text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 touch-manipulation"
              aria-label="Copia ricetta negli appunti">
              <svg lucideCopy aria-hidden="true" class="w-4 h-4 flex-shrink-0"></svg>
              <span>Copia Ricetta</span>
            </button>
          </div>
        </div>
        }
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
export class RecipeDetailSheetComponent {
  private readonly destroyRef = inject(DestroyRef);
  private readonly sheetElRef = viewChild<ElementRef<HTMLElement>>('sheetEl');
  private readonly closeBtnRef = viewChild<ElementRef<HTMLButtonElement>>('closeBtn');

  readonly isOpen = input<boolean>(false);
  readonly recipe = input<SavedRecipe | null>(null);
  readonly closed = output<void>();

  /** True while the sheet plays its exit animation before unmounting. */
  readonly closing = signal(false);
  private closeTimer?: ReturnType<typeof setTimeout>;

  private touchStartY = 0;
  private touchDeltaY = 0;
  private previousOverflow = '';

  readonly parsedSections = computed<RecipeSection[]>(() => {
    const recipe = this.recipe();
    if (!recipe) return [];
    return this.parseRecipeInstructions(recipe.recipe_instructions);
  });

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

  copy() {
    const recipe = this.recipe();
    if (!recipe) return;
    navigator.clipboard.writeText(recipe.recipe_instructions).catch((err) => {
      console.error('Failed to copy recipe: ', err);
    });
  }

  mealTypeLabel(mealType: string): string {
    return MEAL_TYPE_LABELS[mealType] || mealType;
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
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

  private parseRecipeInstructions(instructions: string): RecipeSection[] {
    const lines = instructions.split('\n').filter((line) => line.trim());
    const sections: RecipeSection[] = [];

    let currentBullets: string[] = [];
    let currentNumbered: string[] = [];

    const flushBullets = () => {
      if (currentBullets.length > 0) {
        sections.push({ type: 'bullet', items: [...currentBullets] });
        currentBullets = [];
      }
    };

    const flushNumbered = () => {
      if (currentNumbered.length > 0) {
        sections.push({ type: 'numbered', items: [...currentNumbered] });
        currentNumbered = [];
      }
    };

    lines.forEach((line, index) => {
      // Skip the first line (it's the title, already shown in header)
      if (index === 0) return;

      if (line.startsWith('•')) {
        flushNumbered();
        currentBullets.push(line.substring(1).trim());
      } else if (/^\d+\.\s/.test(line)) {
        flushBullets();
        currentNumbered.push(line.replace(/^\d+\.\s*/, ''));
      } else if (this.isHeading(line)) {
        flushBullets();
        flushNumbered();
        sections.push({ type: 'heading', content: line });
      } else if (line.trim()) {
        flushBullets();
        flushNumbered();
        sections.push({ type: 'paragraph', content: line });
      }
    });

    flushBullets();
    flushNumbered();

    return sections;
  }

  private isHeading(line: string): boolean {
    const trimmed = line.trim();
    return trimmed.length < 60 && !trimmed.endsWith('.') && !trimmed.endsWith(':') && trimmed.length > 0;
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
