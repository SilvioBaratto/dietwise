import { Component, OnInit, ChangeDetectionStrategy, ChangeDetectorRef, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { SettingsService } from '../../services/settings.service';
import { DietService } from '../../services/diet.service';
import { ApiKeyService } from '../../services/api-key.service';
import { DietaConLista, ListaSpesa, Ingrediente, DailyGroup } from '../../models/diet.types';
import { Provider } from '../../models/api-key.types';
import { CostBadgeComponent } from '../../shared/cost-badge/cost-badge.component';

@Component({
  selector: 'app-dashboard',
  imports: [CommonModule, FormsModule, CostBadgeComponent],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DashboardComponent implements OnInit {
  private readonly dietService = inject(DietService);
  private readonly router = inject(Router);
  private readonly settingsService = inject(SettingsService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly apiKeyService = inject(ApiKeyService);

  activeProvider = signal<Provider>('openai');
  activeModel = signal<string>('');

  dietaConLista: DietaConLista | null = null;
  dailyMeals: DailyGroup[] = [];
  error: string | null = null;
  loading = true;       // Start with loading true to prevent flash of empty state
  showGroceryList = false;
  currentGroceryList: ListaSpesa | null = null;

  // Progress tracking for two-step diet generation
  generationProgress: number = 0;  // 0 = not started, 50 = diet generated, 100 = grocery list generated
  generationMessage: string = '';

  // Diet modification properties
  showModifyDialog = false;
  modificationPrompt: string = '';
  modifying = false;

  ngOnInit(): void {
    // First check if user has settings configured
    this.settingsService.hasSettings().subscribe({
      next: (hasSettings) => {
        if (!hasSettings) {
          // Redirect to settings page if user hasn't configured their profile
          this.router.navigate(['/settings'], {
            queryParams: { firstTime: 'true' }
          });
        } else {
          // User has settings, proceed to load diet
          this.loadCurrentWeekDiet();
          this.loadActivePreferences();
        }
      },
      error: (err) => {
        console.error('Error checking user settings', err);
        // On error, still try to load the diet
        this.loadCurrentWeekDiet();
      }
    });
  }

  loadActivePreferences(): void {
    this.apiKeyService.getPreferences().subscribe({
      next: (prefs) => {
        if (prefs.provider) this.activeProvider.set(prefs.provider as Provider);
        if (prefs.model) this.activeModel.set(prefs.model);
        this.cdr.markForCheck();
      },
      error: () => {
        // Silently ignore — cost badge just won't show
      },
    });
  }

  loadCurrentWeekDiet(): void {
    this.error = null;
    this.loading = true;
    // Note: Authorization header is automatically added by authInterceptor
    this.dietService.getCurrentWeekDiet()
      .subscribe({
        next: data => {
          this.dietaConLista = data;
          this.buildDailyGroups();
          this.loading = false;
          this.cdr.markForCheck(); // Trigger change detection
        },
        error: err => {
          console.error('Error fetching current week diet', err);
          // Don't show error banner for 404 (no diet found)
          if (err.status === 404) {
            this.dietaConLista = null;
          } else {
            this.error = err.error?.detail || 'Errore nel recupero della dieta';
          }
          this.loading = false;
          this.cdr.markForCheck(); // Trigger change detection
        }
      });
  }

  generateNewDiet(): void {
    this.error = null;
    this.loading = true;
    this.generationProgress = 0;
    this.generationMessage = 'Generazione del piano settimanale...';
    this.cdr.markForCheck(); // Trigger change detection for loading state

    // Step 1: Create diet (without grocery list)
    this.dietService.createDiet()
      .subscribe({
        next: dietaData => {
          // Diet created successfully (Step 1 complete - 50%)
          this.generationProgress = 50;
          this.generationMessage = 'Piano settimanale creato! Generazione lista della spesa...';
          this.cdr.markForCheck(); // Trigger change detection for progress update

          // Step 2: Generate grocery list
          this.dietService.generateGroceryList(dietaData.id)
            .subscribe({
              next: listaSpesaData => {
                // Grocery list created successfully (Step 2 complete - 100%)
                this.generationProgress = 100;
                this.generationMessage = 'Completato!';

                // Combine the results
                this.dietaConLista = {
                  dieta: dietaData,
                  listaSpesa: listaSpesaData
                };

                this.buildDailyGroups();
                this.loading = false;
                this.cdr.markForCheck(); // Trigger change detection for completion

                // Reset progress after a short delay
                setTimeout(() => {
                  this.generationProgress = 0;
                  this.generationMessage = '';
                  this.cdr.markForCheck(); // Trigger change detection for progress reset
                }, 2000);
              },
              error: err => {
                console.error('Error generating grocery list', err);
                this.error = err.error?.detail || 'Errore nella generazione della lista della spesa';
                this.loading = false;
                this.generationProgress = 0;
                this.generationMessage = '';
                this.cdr.markForCheck(); // Trigger change detection for error state
              }
            });
        },
        error: err => {
          console.error('Error generating new diet', err);
          this.error = err.error?.detail || 'Errore nella generazione della dieta';
          this.loading = false;
          this.generationProgress = 0;
          this.generationMessage = '';
          this.cdr.markForCheck(); // Trigger change detection for error state
        }
      });
  }

  private buildDailyGroups(): void {
    if (!this.dietaConLista) return;

    const { dataInizio, dataFine, pasti } = this.dietaConLista.dieta;
    const start = new Date(dataInizio);
    const end = new Date(dataFine);
    const dates: string[] = [];

    // build array of ISO dates from start→end inclusive
    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      dates.push(d.toISOString().slice(0, 10));
    }

    // Map JavaScript weekday (0=Sunday, 1=Monday, ...) to BAML day enum
    const weekdayToDayEnum: Record<number, string> = {
      0: 'DOMENICA',
      1: 'LUNEDI',
      2: 'MARTEDI',
      3: 'MERCOLEDI',
      4: 'GIOVEDI',
      5: 'VENERDI',
      6: 'SABATO'
    };

    // Group meals by matching actual date to day enum
    this.dailyMeals = dates
      .map(iso => {
        const dateObj = new Date(iso);
        const weekday = dateObj.getDay(); // 0=Sunday, 1=Monday, ..., 6=Saturday
        const dayEnum = weekdayToDayEnum[weekday];

        // Filter meals that match this day's enum
        const meals = pasti.filter(pasto => pasto.day === dayEnum);

        const dayName = dateObj.toLocaleDateString('it-IT', { weekday: 'long' });
        return { date: iso, dayName, meals };
      })
      // Only show days that actually have meals
      .filter(day => day.meals.length > 0);
  }

  navigateToRecipe(mealId: string): void {
    this.router.navigate(['/recipe', mealId]);
  }

  openGroceryList(): void {
    if (this.dietaConLista?.listaSpesa) {
      this.currentGroceryList = this.dietaConLista.listaSpesa;
      this.showGroceryList = true;
      this.cdr.markForCheck();
    }
  }

  closeGroceryList(): void {
    this.showGroceryList = false;
    this.cdr.markForCheck();
  }

  trackByNome(_index: number, ingrediente: Ingrediente): string {
    return ingrediente.nome;
  }

  getMealTypeLabel(tipo: string): string {
    const labels: Record<string, string> = {
      'COLAZIONE': 'Colazione',
      'SPUNTINO_MATTINA': 'Spuntino Mattina',
      'PRANZO': 'Pranzo',
      'SPUNTINO_POMERIGGIO': 'Spuntino Pomeriggio',
      'CENA': 'Cena'
    };
    return labels[tipo] || tipo;
  }

  openModifyDialog(): void {
    this.modificationPrompt = '';
    this.showModifyDialog = true;
    this.cdr.markForCheck();
  }

  closeModifyDialog(): void {
    this.showModifyDialog = false;
    this.modificationPrompt = '';
    this.cdr.markForCheck();
  }

  modifyDiet(): void {
    if (!this.dietaConLista || !this.modificationPrompt.trim()) {
      return;
    }

    this.error = null;
    this.modifying = true;

    const dietId = this.dietaConLista.dieta.id;

    this.dietService.modifyDiet(dietId, this.modificationPrompt.trim())
      .subscribe({
        next: modifiedDietaConLista => {
          // Update with the modified diet and automatically regenerated grocery list
          this.dietaConLista = modifiedDietaConLista;

          // Rebuild daily groups to reflect changes
          this.buildDailyGroups();

          this.modifying = false;
          this.closeModifyDialog();

          // Manually trigger change detection (required for OnPush strategy)
          this.cdr.markForCheck();

          // Log success
          console.log('✅ Diet modified successfully! Dashboard refreshed with new meals and grocery list.');
        },
        error: err => {
          console.error('Error modifying diet', err);
          this.error = err.error?.detail || 'Errore nella modifica della dieta';
          this.modifying = false;
          this.cdr.markForCheck();
        }
      });
  }
}
