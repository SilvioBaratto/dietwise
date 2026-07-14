import { Component, OnInit, signal, computed, inject, ChangeDetectionStrategy } from '@angular/core';

import { RouterModule } from '@angular/router';
import { RecipeService } from '../../services/recipe.service';
import { SavedRecipe } from '../../models/recipe.types';
import { PageHeaderComponent } from '../../shared/page-header/page-header.component';
import { RecipeDetailSheetComponent } from '../../shared/recipe-detail-sheet/recipe-detail-sheet';
import {
  LucideBookOpen,
  LucideAlertTriangle,
  LucideLoader,
  LucideCalendar,
  LucideFlame,
  LucideEye,
  LucideTrash2,
} from '@lucide/angular';

const MEAL_TYPE_ORDER = [
  'COLAZIONE',
  'SPUNTINO_MATTINA',
  'PRANZO',
  'SPUNTINO_POMERIGGIO',
  'CENA',
];

@Component({
  selector: 'app-recipes',
  imports: [
    RouterModule,
    PageHeaderComponent,
    RecipeDetailSheetComponent,
    LucideBookOpen,
    LucideAlertTriangle,
    LucideLoader,
    LucideCalendar,
    LucideFlame,
    LucideEye,
    LucideTrash2,
  ],
  templateUrl: './recipes.component.html',
  styleUrl: './recipes.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RecipesComponent implements OnInit {
  private readonly recipeService = inject(RecipeService);

  // Signals for reactive state
  recipes = signal<SavedRecipe[]>([]);
  loading = signal(true);
  error = signal('');
  deletingRecipeId = signal<string | null>(null);
  selectedRecipe = signal<SavedRecipe | null>(null);
  showModal = signal(false);
  selectedMealType = signal<string | null>(null);

  hasRecipes = computed(() => this.recipes().length > 0);

  availableMealTypes = computed(() => {
    const present = new Set<string>(this.recipes().map((r) => r.meal_type));
    return MEAL_TYPE_ORDER.filter((type) => present.has(type));
  });

  filteredRecipes = computed(() => {
    const type = this.selectedMealType();
    return type ? this.recipes().filter((r) => r.meal_type === type) : this.recipes();
  });

  selectMealType(type: string | null): void {
    this.selectedMealType.set(type);
  }

  ngOnInit() {
    this.loadRecipes();
  }

  loadRecipes() {
    this.loading.set(true);
    this.error.set('');

    // Note: Authorization header is automatically added by authInterceptor
    this.recipeService.getAllRecipes()
      .subscribe({
        next: recipes => {
          this.recipes.set(recipes);
          this.loading.set(false);
        },
        error: err => {
          console.error('Failed to load recipes', err);
          this.error.set('Non è stato possibile caricare le ricette. Riprova più tardi.');
          this.loading.set(false);
        }
      });
  }

  deleteRecipe(recipeId: string, recipeName: string) {
    const confirmed = confirm(`Sei sicuro di voler eliminare "${recipeName}"? Questa azione non può essere annullata.`);

    if (!confirmed) {
      return;
    }

    this.deletingRecipeId.set(recipeId);

    // Note: Authorization header is automatically added by authInterceptor
    this.recipeService.deleteRecipe(recipeId)
      .subscribe({
        next: () => {
          this.recipes.update(recipes => recipes.filter(r => r.id !== recipeId));
          this.deletingRecipeId.set(null);
        },
        error: err => {
          console.error('Failed to delete recipe', err);
          this.error.set(err.error?.detail || 'Non è stato possibile eliminare la ricetta. Riprova più tardi.');
          this.deletingRecipeId.set(null);
        }
      });
  }

  getMealTypeLabel(mealType: string): string {
    const labels: { [key: string]: string } = {
      'COLAZIONE': 'Colazione',
      'SPUNTINO_MATTINA': 'Spuntino Mattina',
      'PRANZO': 'Pranzo',
      'SPUNTINO_POMERIGGIO': 'Spuntino Pomeriggio',
      'CENA': 'Cena'
    };
    return labels[mealType] || mealType;
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  viewRecipe(recipe: SavedRecipe) {
    this.selectedRecipe.set(recipe);
    this.showModal.set(true);
  }

  closeModal() {
    this.showModal.set(false);
    this.selectedRecipe.set(null);
  }

  /**
   * Get a preview of the recipe instructions (first few lines, excluding title)
   */
  getRecipePreview(instructions: string): string {
    const lines = instructions.split('\n').filter(line => line.trim());
    // Skip title (first line) and get content preview
    const contentLines = lines.slice(1).filter(line =>
      !line.startsWith('•') && !/^\d+\./.test(line)
    );
    return contentLines.slice(0, 3).join(' ').substring(0, 150) + (contentLines.length > 3 ? '...' : '');
  }
}
