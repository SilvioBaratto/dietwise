// src/app/services/meal.service.ts
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Pasto } from '../models/diet.types';
import { HtmlStructure } from '../models/recipe.types';

@Injectable({ providedIn: 'root' })
export class MealService {
  private readonly http = inject(HttpClient);

  /**
   * Get a specific meal by ID
   * @param mealId The ID of the meal to fetch
   */
  getMealById(mealId: string): Observable<Pasto> {
    return this.http.get<Pasto>(`${environment.apiUrl}/meals/${mealId}`);
  }

  /**
   * Generate a recipe for a specific meal
   * @param mealId The ID of the meal to generate recipe for
   */
  generateRecipe(mealId: string): Observable<{ recipe: HtmlStructure }> {
    return this.http.get<{ recipe: HtmlStructure }>(`${environment.apiUrl}/meals/${mealId}/recipe`);
  }
}
