import { Component, ChangeDetectionStrategy, computed, input, inject } from '@angular/core';
import { CostEstimateService } from '../../services/cost-estimate.service';
import { Provider } from '../../models/api-key.types';

@Component({
  selector: 'app-cost-badge',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (costEstimate()) {
      <div class="flex items-center gap-2 px-3 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-600"
        title="Stima indicativa basata sui prezzi pubblici del provider. Il costo effettivo dipende dalla lunghezza della risposta e dai prezzi correnti del provider.">
        <span class="flex-shrink-0" aria-hidden="true">&#x1f4b0;</span>
        <span>Costo stimato: <span class="font-semibold text-gray-900">{{ costEstimate() }}</span></span>
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
