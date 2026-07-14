// src/app/components/weekly/recipe-details.component.ts

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
import { MealService } from '../../../services/meal.service';
import { RecipeService } from '../../../services/recipe.service';
import { Pasto } from '../../../models/diet.types';
import { HtmlStructure, SavedRecipe } from '../../../models/recipe.types';

@Component({
  selector: 'app-recipe-details',
  imports: [CommonModule, RouterModule],
  templateUrl: './recipe-details.component.html',
  styleUrls: ['./recipe-details.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RecipeDetailsComponent implements OnInit {
  private readonly mealService = inject(MealService);
  private readonly recipeService = inject(RecipeService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  // Signals for reactive state
  meal = signal<Pasto | undefined>(undefined);
  generatedRecipe = signal<HtmlStructure>({
    h1: '',
    h2: [],
    p: [],
    ul: [],
    ol: [],
  });
  savedRecipes = signal<SavedRecipe[]>([]);
  error = signal('');
  loading = signal(true);
  generating = signal(false);
  savingRecipe = signal(false);
  loadingSavedRecipes = signal(false);
  saveSuccess = signal(false);

  // Convert route params to signal
  private params = toSignal(this.route.paramMap);
  private mealId = computed(() => this.params()?.get('meal_id') ?? null);

  // Computed signal for recipe text conversion
  recipeText = computed(() => {
    const recipe = this.generatedRecipe();
    if (!recipe || !recipe.h1) return '';

    let text = `${recipe.h1}\n\n`;

    if (recipe.h2 && recipe.h2.length > 0) {
      recipe.h2.forEach((heading, idx) => {
        if (idx > 0) text += `\n${heading}\n`;
      });
    }

    if (recipe.p && recipe.p.length > 0) {
      recipe.p.forEach((paragraph) => {
        text += `\n${paragraph}\n`;
      });
    }

    if (recipe.ul && recipe.ul.length > 0) {
      text += '\n';
      recipe.ul.forEach((item) => {
        text += `• ${item}\n`;
      });
    }

    if (recipe.ol && recipe.ol.length > 0) {
      text += '\n';
      recipe.ol.forEach((step, idx) => {
        text += `${idx + 1}. ${step}\n`;
      });
    }

    return text;
  });

  ngOnInit() {
    const id = this.mealId();
    if (!id) {
      this.error.set('No meal ID provided');
      this.loading.set(false);
      return;
    }
    this.fetchMeal(id);
  }

  private fetchMeal(id: string) {
    this.loading.set(true);
    this.error.set('');
    // Note: Authorization header is automatically added by authInterceptor
    this.mealService.getMealById(id).subscribe({
      next: (pasto) => {
        this.meal.set(pasto);
        this.loading.set(false);
        // Load saved recipes for this meal
        this.loadSavedRecipes();
      },
      error: (err) => {
        console.error('Failed to load meal', err);
        this.error.set(
          err.status === 404
            ? 'Meal not found.'
            : 'Failed to load meal. Please try again.'
        );
        this.loading.set(false);
      },
    });
  }

  generateRecipe() {
    const id = this.mealId();
    if (!id) return;
    this.generating.set(true);
    // Note: Authorization header is automatically added by authInterceptor
    this.mealService.generateRecipe(id)
      .subscribe({
        next: (res) => {
          this.generatedRecipe.set(res.recipe);
          this.generating.set(false);
        },
        error: (err) => {
          console.error('Failed to generate recipe', err);
          this.error.set('Could not generate recipe. Please try again.');
          this.generating.set(false);
        },
      });
  }

  goBack() {
    this.router.navigate(['/weekly'], { relativeTo: this.route });
  }

  getMealTypeLabel(tipo: string): string {
    const labels: { [key: string]: string } = {
      COLAZIONE: 'Colazione',
      SPUNTINO_MATTINA: 'Spuntino Mattina',
      PRANZO: 'Pranzo',
      SPUNTINO_POMERIGGIO: 'Spuntino Pomeriggio',
      CENA: 'Cena',
    };
    return labels[tipo] || tipo;
  }

  copyRecipe() {
    const text = this.recipeText();
    if (text) {
      navigator.clipboard
        .writeText(text)
        .then(() => {
          console.log('Recipe copied to clipboard');
        })
        .catch((err) => {
          console.error('Failed to copy recipe: ', err);
        });
    }
  }

  saveRecipe() {
    const meal = this.meal();
    const text = this.recipeText();

    if (!meal || !text) {
      return;
    }

    this.savingRecipe.set(true);
    this.saveSuccess.set(false);

    const saveData = {
      recipe_name: meal.tipoPasto.ricetta,
      recipe_instructions: text,
      meal_type: meal.tipoPasto.tipo,
      calories: meal.calorie,
    };

    // Note: Authorization header is automatically added by authInterceptor
    this.recipeService.saveRecipe(saveData)
      .subscribe({
        next: () => {
          this.savingRecipe.set(false);
          this.saveSuccess.set(true);
          // Load saved recipes after saving
          this.loadSavedRecipes();
          // Hide success message after 3 seconds
          setTimeout(() => {
            this.saveSuccess.set(false);
          }, 3000);
        },
        error: (err) => {
          console.error('Failed to save recipe', err);
          this.error.set(
            'Non è stato possibile salvare la ricetta. Riprova più tardi.'
          );
          this.savingRecipe.set(false);
        },
      });
  }

  loadSavedRecipes() {
    const meal = this.meal();
    if (!meal) return;

    this.loadingSavedRecipes.set(true);

    // Note: Authorization header is automatically added by authInterceptor
    this.recipeService.getRecipesByName(meal.tipoPasto.ricetta)
      .subscribe({
        next: (recipes) => {
          this.savedRecipes.set(recipes);
          this.loadingSavedRecipes.set(false);
        },
        error: (err) => {
          console.error('Failed to load saved recipes', err);
          this.loadingSavedRecipes.set(false);
        },
      });
  }

  viewSavedRecipe(recipe: SavedRecipe) {
    // Parse the saved recipe text back into HtmlStructure format
    const lines = recipe.recipe_instructions
      .split('\n')
      .filter((line) => line.trim());

    const parsed: HtmlStructure = {
      h1: lines[0] || '',
      h2: [],
      p: [],
      ul: [],
      ol: [],
    };

    // Simple parsing - you might want to enhance this
    lines.slice(1).forEach((line) => {
      if (line.startsWith('•')) {
        parsed.ul.push(line.substring(1).trim());
      } else if (/^\d+\./.test(line)) {
        parsed.ol.push(line.replace(/^\d+\.\s*/, ''));
      } else if (line.length < 50 && !line.endsWith('.')) {
        // Likely a heading
        parsed.h2.push(line);
      } else {
        parsed.p.push(line);
      }
    });

    this.generatedRecipe.set(parsed);
  }
}
