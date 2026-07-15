import { ChangeDetectionStrategy, Component, computed, input, model, signal } from '@angular/core';

/**
 * Editable combobox: native <input list> + <datalist>. Shows curated
 * suggestions but always accepts a freely typed value — the WAI-ARIA
 * "editable combobox, list autocomplete with manual selection" pattern,
 * implemented with zero JS since this codebase has no CDK/positioning
 * primitives to build a hand-rolled ARIA widget on top of.
 */
@Component({
  selector: 'app-editable-select',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="space-y-2 sm:space-y-3">
      <label [for]="id()" class="flex items-center gap-2 text-sm font-semibold text-gray-700">
        {{ label() }}
        @if (required()) {
          <span class="text-red-500" aria-label="obbligatorio">*</span>
        }
      </label>
      <input
        type="text"
        [id]="id()"
        [attr.list]="id() + '-options'"
        [value]="value()"
        (input)="onInput($any($event.target).value)"
        (blur)="touched.set(true)"
        [placeholder]="placeholder()"
        [disabled]="disabled()"
        autocomplete="off"
        [attr.aria-describedby]="helpText() ? id() + '-help' : null"
        class="w-full px-4 py-4 min-h-[48px] text-base border rounded-xl
               focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-violet-500
               hover:border-gray-400 transition-colors duration-200
               disabled:opacity-50 disabled:cursor-not-allowed"
        [class.border-gray-300]="!invalid()"
        [class.border-red-300]="invalid()"
      />
      <datalist [id]="id() + '-options'">
        @for (s of suggestions(); track s) {
          <option [value]="s"></option>
        }
      </datalist>
      @if (helpText()) {
        <p [id]="id() + '-help'" class="text-xs text-gray-500">{{ helpText() }}</p>
      }
      @if (invalid()) {
        <p class="text-sm text-red-600 mt-1">Questo campo è obbligatorio</p>
      }
    </div>
  `,
})
export class EditableSelectComponent {
  id = input.required<string>();
  label = input.required<string>();
  suggestions = input<string[]>([]);
  placeholder = input<string>('');
  helpText = input<string | null>(null);
  disabled = input<boolean>(false);
  required = input<boolean>(false);
  value = model<string>('');

  touched = signal(false);
  invalid = computed(() => this.required() && this.touched() && !this.value().trim());

  onInput(v: string): void {
    this.value.set(v);
  }
}
