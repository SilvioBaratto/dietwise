// src/app/models/recipe.types.ts

export interface SavedRecipe {
  readonly id: string;
  readonly recipe_name: string;
  readonly recipe_instructions: string;
  readonly meal_type: string;
  readonly calories: number;
  readonly created_at: string;
}

export interface HtmlStructure {
  readonly h1: string;
  readonly h2: string[];
  readonly p: string[];
  readonly ul: string[];
  readonly ol: string[];
}

export interface CreateRecipeRequest {
  readonly recipe_name: string;
  readonly recipe_instructions: string;
  readonly meal_type: string;
  readonly calories: number;
}
