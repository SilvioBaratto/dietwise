// src/app/weekly-details/weekly-details.component.ts
import {
  Component,
  OnInit,
  signal,
  computed,
  inject,
  ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { DietService } from '../../../services/diet.service';
import { DietaSettimanale, Pasto } from '../../../models/diet.types';

interface DayGroup {
  day: string;
  dayName: string;
  meals: Pasto[];
}

@Component({
  selector: 'app-weekly-details',
  imports: [CommonModule, RouterModule],
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

  // Computed signals for derived state
  totalCalories = computed(() => {
    const dietData = this.diet();
    return (
      dietData?.pasti.reduce((total, pasto) => total + pasto.calorie, 0) || 0
    );
  });

  uniqueDays = computed(() => {
    const dietData = this.diet();
    if (!dietData) return 0;

    // Count unique days from the pasti
    const uniqueDays = new Set(dietData.pasti.map((p) => p.day));
    return uniqueDays.size;
  });

  uniqueIngredients = computed(() => {
    const dietData = this.diet();
    if (!dietData) return 0;

    const uniqueIngredients = new Set<string>();
    dietData.pasti.forEach((pasto) => {
      // Parse comma-separated ingredient string
      const ingredients = pasto.ingredienti.split(',').map((i) => i.trim());
      ingredients.forEach((ing) => {
        // Extract ingredient name from formats like "200 gr di riso" or "150 ml di latte"
        // Look for "di " (of) which indicates the ingredient name follows
        const diIndex = ing.toLowerCase().indexOf(' di ');
        let name = '';

        if (diIndex !== -1) {
          // Extract everything after "di "
          name = ing
            .substring(diIndex + 4)
            .trim()
            .toLowerCase();
        } else {
          // No "di" found - try to extract last word(s) after units
          // Remove common units and numbers to get ingredient name
          name = ing
            .replace(/\d+(\.\d+)?/g, '') // Remove numbers
            .replace(
              /\b(gr|g|kg|ml|l|pz|cucchiai|cucchiaio|tazza|tazze)\b/gi,
              ''
            ) // Remove units
            .trim()
            .toLowerCase();
        }

        if (name) uniqueIngredients.add(name);
      });
    });

    return uniqueIngredients.size;
  });

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

  // Expose computed signals as methods for template compatibility
  getTotalCalories(): number {
    return this.totalCalories();
  }

  getUniqueDays(): number {
    return this.uniqueDays();
  }

  getUniqueIngredients(): number {
    return this.uniqueIngredients();
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

  groupMealsByDay(): DayGroup[] {
    return this.groupedMealsByDay();
  }
}
