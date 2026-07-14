// src/app/weekly-details/weekly-details.component.ts
import {
  Component,
  OnInit,
  signal,
  computed,
  effect,
  inject,
  ChangeDetectionStrategy,
} from '@angular/core';

import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { DietService } from '../../../services/diet.service';
import { DietaSettimanale, Pasto } from '../../../models/diet.types';
import {
  LucideAlertTriangle,
  LucideCalendar,
  LucideZap,
  LucideChevronRight,
  LucideEye,
} from '@lucide/angular';

const MEAL_TYPE_ORDER = [
  'COLAZIONE',
  'SPUNTINO_MATTINA',
  'PRANZO',
  'SPUNTINO_POMERIGGIO',
  'CENA',
];

@Component({
  selector: 'app-weekly-details',
  imports: [
    RouterModule,
    LucideAlertTriangle,
    LucideCalendar,
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
  selectedDay = signal<string | null>(null);
  selectedMealType = signal<string | null>(null);

  // Convert route params to signal
  private params = toSignal(this.route.paramMap);
  private dietId = computed(() => this.params()?.get('diet_id') ?? null);

  // Default to the first day with meals once the diet loads
  private readonly initSelectedDay = effect(() => {
    const groups = this.groupedMealsByDay();
    if (!this.selectedDay() && groups.length > 0) {
      this.selectedDay.set(groups[0].day);
    }
  });

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
          const orderA = MEAL_TYPE_ORDER.indexOf(a.tipoPasto.tipo);
          const orderB = MEAL_TYPE_ORDER.indexOf(b.tipoPasto.tipo);
          return (orderA === -1 ? 999 : orderA) - (orderB === -1 ? 999 : orderB);
        }),
      }))
      .sort((a, b) => dayOrder.indexOf(a.day) - dayOrder.indexOf(b.day));
  });

  selectedDayGroup = computed(() => {
    const groups = this.groupedMealsByDay();
    return groups.find((g) => g.day === this.selectedDay()) ?? groups[0] ?? null;
  });

  availableMealTypes = computed(() => {
    const group = this.selectedDayGroup();
    if (!group) return [];
    const present = new Set<string>(group.meals.map((m) => m.tipoPasto.tipo));
    return MEAL_TYPE_ORDER.filter((type) => present.has(type));
  });

  filteredMeals = computed(() => {
    const group = this.selectedDayGroup();
    if (!group) return [];
    const type = this.selectedMealType();
    return type ? group.meals.filter((m) => m.tipoPasto.tipo === type) : group.meals;
  });

  selectDay(day: string): void {
    this.selectedDay.set(day);
  }

  selectMealType(type: string | null): void {
    this.selectedMealType.set(type);
  }

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

  getShortDayName(dayEnum: string): string {
    const shortNames: Record<string, string> = {
      LUNEDI: 'Lun',
      MARTEDI: 'Mar',
      MERCOLEDI: 'Mer',
      GIOVEDI: 'Gio',
      VENERDI: 'Ven',
      SABATO: 'Sab',
      DOMENICA: 'Dom',
    };
    return shortNames[dayEnum] || dayEnum.slice(0, 3);
  }
}
