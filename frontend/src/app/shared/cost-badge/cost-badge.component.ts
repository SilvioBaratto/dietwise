import { Component, ChangeDetectionStrategy, computed, input, inject } from '@angular/core';
import { CostEstimateService } from '../../services/cost-estimate.service';
import { Provider } from '../../models/api-key.types';

@Component({
  selector: 'app-cost-badge',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (costEstimate()) {
      <div class="p-4 bg-amber-50 border border-amber-200 rounded-xl">
        <div class="flex items-start gap-3">
          <span class="text-amber-600 text-lg flex-shrink-0 mt-0.5" aria-hidden="true">&#x1f4b0;</span>
          <div class="text-sm sm:text-base text-amber-900">
            <p class="font-semibold mb-1">
              Costo stimato per generazione: <span class="text-amber-700">{{ costEstimate() }}</span>
            </p>
            <p class="text-xs sm:text-sm text-amber-700">
              Stima indicativa basata sui prezzi pubblici del provider.
              Il costo effettivo dipende dalla lunghezza della risposta e dai prezzi correnti del provider.
            </p>
          </div>
        </div>
      </div>
    }
  `,
})
export class CostBadgeComponent {
  provider = input.required<Provider>();
  model = input.required<string>();

  private readonly costService = inject(CostEstimateService);

  costEstimate = computed(() => this.costService.getEstimate(this.provider(), this.model()));
}
