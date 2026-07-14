import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import { LucideArrowLeft } from '@lucide/angular';

@Component({
  selector: 'app-page-header',
  imports: [LucideArrowLeft],
  templateUrl: './page-header.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PageHeaderComponent {
  title = input.required<string>();
  subtitle = input<string | null>(null);
  backLabel = input<string | null>(null);
  back = output<void>();
}
