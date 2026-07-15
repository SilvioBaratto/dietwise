// src/app/services/recipe.service.ts
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';
import { SavedRecipe, CreateRecipeRequest } from '../models/recipe.types';
import { RequestCache } from './request-cache';

@Injectable({ providedIn: 'root' })
export class RecipeService {
  private readonly http = inject(HttpClient);

  private readonly allRecipesCache = new RequestCache<SavedRecipe[]>();

  /**
   * Get all saved recipes for the current user
   */
  getAllRecipes(): Observable<SavedRecipe[]> {
    return this.allRecipesCache.get('all', () =>
      this.http.get<SavedRecipe[]>(`${environment.apiUrl}/recipes`),
    );
  }

  /**
   * Delete a specific saved recipe
   * @param recipeId The ID of the recipe to delete
   */
  deleteRecipe(recipeId: string): Observable<void> {
    return this.http.delete<void>(`${environment.apiUrl}/recipes/${recipeId}`).pipe(
      tap(() => this.allRecipesCache.clear()),
    );
  }

  /**
   * Save a new recipe
   * @param recipeData The recipe data to save
   */
  saveRecipe(recipeData: CreateRecipeRequest): Observable<SavedRecipe> {
    return this.http.post<SavedRecipe>(`${environment.apiUrl}/recipes`, recipeData).pipe(
      tap(() => this.allRecipesCache.clear()),
    );
  }

  /**
   * Get saved recipes by recipe name
   * @param recipeName The name of the recipe to search for
   */
  getRecipesByName(recipeName: string): Observable<SavedRecipe[]> {
    const encodedName = encodeURIComponent(recipeName);
    return this.http.get<SavedRecipe[]>(`${environment.apiUrl}/recipes/by-name/${encodedName}`);
  }

  /** Clears every cached GET response owned by this service. */
  clearCache(): void {
    this.allRecipesCache.clear();
  }
}
