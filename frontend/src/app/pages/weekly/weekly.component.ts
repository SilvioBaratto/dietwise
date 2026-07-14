// src/app/weekly/weekly.component.ts
import { Component, OnInit, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { DietService } from '../../services/diet.service';
import { DietSummary, ListaSpesa, Ingrediente } from '../../models/diet.types';

@Component({
  selector: 'app-weekly',
  imports: [CommonModule, RouterModule],
  templateUrl: './weekly.component.html',
  styleUrls: ['./weekly.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WeeklyComponent implements OnInit {
  private readonly dietService = inject(DietService);
  public readonly router = inject(Router);

  // Convert to signals for OnPush compatibility
  diets = signal<DietSummary[]>([]);
  error = signal<string>('');
  loading = signal<boolean>(true);
  showGroceryList = signal<boolean>(false);
  currentGroceryList = signal<ListaSpesa | null>(null);
  groceryListLoading = signal<boolean>(false);

  ngOnInit(): void {
    this.loading.set(true);
    // Note: Authorization header is automatically added by authInterceptor
    this.dietService.getAllDiets()
      .subscribe({
        next: (data) => {
          this.diets.set(data);
          this.loading.set(false);
        },
        error: (err) => {
          console.error('Failed to load diets', err);
          this.error.set('Could not load your diets. Please try again later.');
          this.loading.set(false);
        }
      });
  }

  viewDiet(dietId: string): void {
    this.router.navigate(['/weekly', dietId]);
  }

  viewGroceryList(dietId: string): void {
    this.groceryListLoading.set(true);
    // Note: Authorization header is automatically added by authInterceptor
    this.dietService.getGroceryListById(dietId)
      .subscribe({
        next: (data) => {
          this.currentGroceryList.set(data);
          this.showGroceryList.set(true);
          this.groceryListLoading.set(false);
        },
        error: (err) => {
          console.error('Failed to load grocery list', err);
          this.error.set('Could not load the grocery list. Please try again later.');
          this.groceryListLoading.set(false);
        }
      });
  }

  closeGroceryList(): void {
    this.showGroceryList.set(false);
    this.currentGroceryList.set(null);
  }

  trackByNome(_index: number, ingrediente: Ingrediente): string {
    return ingrediente.nome;
  }

  deleteDiet(dietId: string, dietName: string | undefined): void {
    const name = dietName || 'questo piano';
    const confirmed = confirm(`Sei sicuro di voler eliminare ${name}? Questa azione non può essere annullata.`);

    if (!confirmed) {
      return;
    }

    // Note: Authorization header is automatically added by authInterceptor
    this.dietService.deleteDiet(dietId)
      .subscribe({
        next: () => {
          // Remove the deleted diet from the list using signal update
          this.diets.update(currentDiets => currentDiets.filter(d => d.id !== dietId));
          console.log('Diet deleted successfully');
        },
        error: (err) => {
          console.error('Failed to delete diet', err);
          this.error.set(err.error?.detail || 'Non è stato possibile eliminare il piano. Riprova più tardi.');
        }
      });
  }
}
