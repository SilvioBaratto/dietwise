// src/app/services/diet.service.ts
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';
import { DietaConLista, DietaSettimanale, ListaSpesa, ModifyDietRequest, DietSummary } from '../models/diet.types';
import { RequestCache } from './request-cache';
import { MealService } from './meal.service';

@Injectable({ providedIn: 'root' })
export class DietService {
  private readonly http = inject(HttpClient);
  private readonly mealService = inject(MealService);

  private readonly currentWeekCache = new RequestCache<DietaConLista>();
  private readonly listCache = new RequestCache<DietSummary[]>();
  private readonly dietByIdCache = new RequestCache<DietaSettimanale>();
  private readonly groceryByIdCache = new RequestCache<ListaSpesa>();

  /**
   * Get the current week's diet with grocery list
   * Returns 404 if no diet exists for the current week
   */
  getCurrentWeekDiet(): Observable<DietaConLista> {
    return this.currentWeekCache.get('current_week', () =>
      this.http.get<DietaConLista>(`${environment.apiUrl}/diet/current_week`),
    );
  }

  /**
   * Create a new weekly diet
   * This generates the diet plan without the grocery list
   */
  createDiet(): Observable<DietaSettimanale> {
    return this.http.post<DietaSettimanale>(`${environment.apiUrl}/diet/create_diet`, {}).pipe(
      tap(() => {
        this.currentWeekCache.clear();
        this.listCache.clear();
        this.mealService.clearCache();
      }),
    );
  }

  /**
   * Generate grocery list for a specific diet
   * @param dietId The ID of the diet to generate grocery list for
   */
  generateGroceryList(dietId: string): Observable<ListaSpesa> {
    return this.http.post<ListaSpesa>(`${environment.apiUrl}/diet/${dietId}/grocery-list`, {}).pipe(
      tap(() => {
        this.currentWeekCache.clear();
        this.groceryByIdCache.delete(dietId);
      }),
    );
  }

  /**
   * Modify an existing diet with a natural language prompt
   * Returns the modified diet with automatically regenerated grocery list
   * @param dietId The ID of the diet to modify
   * @param modificationPrompt Natural language description of desired changes
   */
  modifyDiet(dietId: string, modificationPrompt: string): Observable<DietaConLista> {
    const request: ModifyDietRequest = { modification_prompt: modificationPrompt };
    return this.http.patch<DietaConLista>(`${environment.apiUrl}/diet/${dietId}/modify`, request).pipe(
      tap(() => {
        this.currentWeekCache.clear();
        this.listCache.clear();
        this.dietByIdCache.delete(dietId);
        this.groceryByIdCache.delete(dietId);
        this.mealService.clearCache();
      }),
    );
  }

  /**
   * Get list of all diets for the current user
   * Returns summary information for each diet
   */
  getAllDiets(): Observable<DietSummary[]> {
    return this.listCache.get('list', () =>
      this.http.get<DietSummary[]>(`${environment.apiUrl}/diet/list`),
    );
  }

  /**
   * Get grocery list for a specific diet by ID
   * @param dietId The ID of the diet to get grocery list for
   */
  getGroceryListById(dietId: string): Observable<ListaSpesa> {
    return this.groceryByIdCache.get(dietId, () =>
      this.http.get<ListaSpesa>(`${environment.apiUrl}/diet/${dietId}/grocery-list`),
    );
  }

  /**
   * Delete a specific diet
   * @param dietId The ID of the diet to delete
   */
  deleteDiet(dietId: string): Observable<void> {
    return this.http.delete<void>(`${environment.apiUrl}/diet/${dietId}`).pipe(
      tap(() => {
        this.currentWeekCache.clear();
        this.listCache.clear();
        this.dietByIdCache.delete(dietId);
        this.groceryByIdCache.delete(dietId);
        this.mealService.clearCache();
      }),
    );
  }

  /**
   * Get a specific diet by ID
   * @param dietId The ID of the diet to fetch
   */
  getDietById(dietId: string): Observable<DietaSettimanale> {
    return this.dietByIdCache.get(dietId, () =>
      this.http.get<DietaSettimanale>(`${environment.apiUrl}/diet/${dietId}`),
    );
  }

  /** Clears every cached GET response owned by this service. */
  clearCache(): void {
    this.currentWeekCache.clear();
    this.listCache.clear();
    this.dietByIdCache.clear();
    this.groceryByIdCache.clear();
  }
}
