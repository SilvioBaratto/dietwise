// src/app/weekly/weekly.component.ts
import { Component, OnInit, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { DietService } from '../../services/diet.service';
import { DietSummary, ListaSpesa } from '../../models/diet.types';
import { PageHeaderComponent } from '../../shared/page-header/page-header.component';
import { GroceryListSheetComponent } from '../../shared/grocery-list-sheet/grocery-list-sheet';
import {
  LucideAlertTriangle,
  LucideClipboard,
  LucideCalendar,
  LucideEye,
  LucideTrash2,
  LucideInbox,
  LucideArrowLeft,
} from '@lucide/angular';

@Component({
  selector: 'app-weekly',
  imports: [
    CommonModule,
    RouterModule,
    PageHeaderComponent,
    GroceryListSheetComponent,
    LucideAlertTriangle,
    LucideClipboard,
    LucideCalendar,
    LucideEye,
    LucideTrash2,
    LucideInbox,
    LucideArrowLeft,
  ],
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
  groceryListLoadingId = signal<string | null>(null);

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
    this.groceryListLoadingId.set(dietId);
    // Note: Authorization header is automatically added by authInterceptor
    this.dietService.getGroceryListById(dietId)
      .subscribe({
        next: (data) => {
          this.currentGroceryList.set(data);
          this.showGroceryList.set(true);
          this.groceryListLoadingId.set(null);
        },
        error: (err) => {
          console.error('Failed to load grocery list', err);
          this.error.set('Could not load the grocery list. Please try again later.');
          this.groceryListLoadingId.set(null);
        }
      });
  }

  closeGroceryList(): void {
    this.showGroceryList.set(false);
    this.currentGroceryList.set(null);
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
