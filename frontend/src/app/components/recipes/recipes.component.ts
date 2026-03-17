import { Component, OnInit, signal, computed, inject, ChangeDetectionStrategy } from '@angular/core';

import { RouterModule } from '@angular/router';
import { RecipeService } from '../../services/recipe.service';
import { SavedRecipe } from '../../models/recipe.types';

@Component({
  selector: 'app-recipes',
  imports: [RouterModule],
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

  // Computed signal for recipe count
  recipeCount = computed(() => this.recipes().length);
  hasRecipes = computed(() => this.recipes().length > 0);

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

  getMealTypeColor(mealType: string): string {
    const colors: { [key: string]: string } = {
      'COLAZIONE': 'bg-amber-100 text-amber-800',
      'SPUNTINO_MATTINA': 'bg-green-100 text-green-800',
      'PRANZO': 'bg-blue-100 text-blue-800',
      'SPUNTINO_POMERIGGIO': 'bg-green-100 text-green-800',
      'CENA': 'bg-purple-100 text-purple-800'
    };
    return colors[mealType] || 'bg-gray-100 text-gray-800';
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

  copyRecipe() {
    const recipe = this.selectedRecipe();
    if (recipe) {
      navigator.clipboard.writeText(recipe.recipe_instructions).then(() => {
        console.log('Recipe copied to clipboard');
      }).catch(err => {
        console.error('Failed to copy recipe: ', err);
      });
    }
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

  /**
   * Parse recipe instructions text into structured sections for rendering
   */
  parseRecipeInstructions(instructions: string): RecipeSection[] {
    const lines = instructions.split('\n').filter(line => line.trim());
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

    // Flush any remaining items
    flushBullets();
    flushNumbered();

    return sections;
  }

  /**
   * Determine if a line is likely a heading (short, no period at end)
   */
  private isHeading(line: string): boolean {
    const trimmed = line.trim();
    return trimmed.length < 60 &&
           !trimmed.endsWith('.') &&
           !trimmed.endsWith(':') &&
           trimmed.length > 0;
  }
}

interface RecipeSection {
  type: 'heading' | 'paragraph' | 'bullet' | 'numbered';
  content?: string;
  items?: string[];
}
