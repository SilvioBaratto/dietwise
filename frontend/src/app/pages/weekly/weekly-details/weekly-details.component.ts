// src/app/weekly-details/weekly-details.component.ts
import {
  Component,
  OnInit,
  signal,
  computed,
  inject,
  ChangeDetectionStrategy,
} from '@angular/core';

import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { DietService } from '../../../services/diet.service';
import { DailyGroup, DietaSettimanale, Pasto } from '../../../models/diet.types';
import {
  LucideAlertTriangle,
  LucideCalendar,
  LucideClock,
  LucideZap,
  LucideChevronRight,
  LucideEye,
} from '@lucide/angular';

@Component({
  selector: 'app-weekly-details',
  imports: [
    RouterModule,
    LucideAlertTriangle,
    LucideCalendar,
    LucideClock,
    LucideZap,
    LucideChevronRight,
    LucideEye,
  ],
  templateUrl: './weekly-details.component.html',
  styleUrls: ['./weekly-details.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class WeeklyDetailsComponent implements OnInit {
  private readonly dietService = inject(DietService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  // Signals for reactive state
  diet = signal<DietaSettimanale | undefined>(undefined);
  error = signal('');
  loading = signal(true);

  // Convert route params to signal
  private params = toSignal(this.route.paramMap);
  private dietId = computed(() => this.params()?.get('diet_id') ?? null);

  ngOnInit() {
    const id = this.dietId();
    if (!id) {
      this.error.set('No diet ID provided');
      this.loading.set(false);
      return;
    }
    this.fetchDiet(id);
  }

  groupedMealsByDay = computed(() => {
    const dietData = this.diet();
    if (!dietData) return [];

    // Group meals by day enum
    const grouped = new Map<string, Pasto[]>();

    dietData.pasti.forEach((pasto) => {
      const dayMeals = grouped.get(pasto.day) || [];
      dayMeals.push(pasto);
      grouped.set(pasto.day, dayMeals);
    });

    // Sort meals within each day by meal type order
    const mealTypeOrder: Record<string, number> = {
      COLAZIONE: 1,
      SPUNTINO_MATTINA: 2,
      PRANZO: 3,
      SPUNTINO_POMERIGGIO: 4,
      CENA: 5,
    };

    // Day order for sorting
    const dayOrder = [
      'LUNEDI',
      'MARTEDI',
      'MERCOLEDI',
      'GIOVEDI',
      'VENERDI',
      'SABATO',
      'DOMENICA',
    ];

    // Convert to array and sort by day
    return Array.from(grouped.entries())
      .map(([day, meals]) => ({
        day,
        dayName: this.getDayName(day),
        meals: meals.sort((a, b) => {
          const orderA = mealTypeOrder[a.tipoPasto.tipo] || 999;
          const orderB = mealTypeOrder[b.tipoPasto.tipo] || 999;
          return orderA - orderB;
        }),
      }))
      .sort((a, b) => dayOrder.indexOf(a.day) - dayOrder.indexOf(b.day));
  });

  private fetchDiet(id: string) {
    this.loading.set(true);
    // Note: Authorization header is automatically added by authInterceptor
    this.dietService.getDietById(id).subscribe({
      next: (diet) => {
        this.diet.set(diet);
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Could not load diet', err);
        this.error.set(
          err.status === 404
            ? 'Diet not found.'
            : 'Failed to load diet. Please try again.'
        );
        this.loading.set(false);
      },
    });
  }

  viewRecipe(mealId: string) {
    this.router.navigate(['/recipe', mealId]);
  }

  getDayName(dayEnum: string): string {
    const dayNames: Record<string, string> = {
      LUNEDI: 'Lunedì',
      MARTEDI: 'Martedì',
      MERCOLEDI: 'Mercoledì',
      GIOVEDI: 'Giovedì',
      VENERDI: 'Venerdì',
      SABATO: 'Sabato',
      DOMENICA: 'Domenica',
    };
    return dayNames[dayEnum] || dayEnum;
  }

  getMealTypeLabel(tipo: string): string {
    const labels: Record<string, string> = {
      COLAZIONE: 'Colazione',
      SPUNTINO_MATTINA: 'Spuntino Mattina',
      PRANZO: 'Pranzo',
      SPUNTINO_POMERIGGIO: 'Spuntino Pomeriggio',
      CENA: 'Cena',
    };
    return labels[tipo] || tipo;
  }

  groupMealsByDay(): DailyGroup[] {
    return this.groupedMealsByDay();
  }
}
