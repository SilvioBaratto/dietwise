// src/app/services/meal.service.ts
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Pasto } from '../models/diet.types';
import { HtmlStructure } from '../models/recipe.types';
import { RequestCache } from './request-cache';

@Injectable({ providedIn: 'root' })
export class MealService {
  private readonly http = inject(HttpClient);

  private readonly mealByIdCache = new RequestCache<Pasto>();

  /**
   * Get a specific meal by ID
   * @param mealId The ID of the meal to fetch
   */
  getMealById(mealId: string): Observable<Pasto> {
    return this.mealByIdCache.get(mealId, () =>
      this.http.get<Pasto>(`${environment.apiUrl}/meals/${mealId}`),
    );
  }

  /**
   * Generate a recipe for a specific meal
   * Never cached - this is an LLM generation call, not a stable read.
   * @param mealId The ID of the meal to generate recipe for
   */
  generateRecipe(mealId: string): Observable<{ recipe: HtmlStructure }> {
    return this.http.get<{ recipe: HtmlStructure }>(`${environment.apiUrl}/meals/${mealId}/recipe`);
  }

  /** Clears every cached GET response owned by this service. */
  clearCache(): void {
    this.mealByIdCache.clear();
  }
}
