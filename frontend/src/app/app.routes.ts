// src/app/app.routes.ts

import { Routes } from '@angular/router';
import { authGuard, guestGuard } from './guards/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    canActivate: [guestGuard],
    loadComponent: () => import('./auth/login/login.component').then(m => m.LoginComponent)
  },
  {
    path: 'auth/callback',
    loadComponent: () => import('./services/auth-callback.component').then(m => m.AuthCallbackComponent)
  },
  {
    path: 'pending-approval',
    loadComponent: () => import('./auth/pending-approval/pending-approval.component').then(m => m.PendingApprovalComponent)
  },
  {
    path: 'accept-terms',
    loadComponent: () => import('./auth/accept-terms/accept-terms.component').then(m => m.AcceptTermsComponent)
  },

  {
    path: '',
    canActivate: [authGuard],
    children: [
      {
        path: '',
        loadComponent: () => import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent)
      },
      {
        path: 'weekly',
        loadComponent: () => import('./pages/weekly/weekly.component').then(m => m.WeeklyComponent)
      },
      {
        path: 'weekly/:diet_id',
        loadComponent: () => import('./pages/weekly/weekly-details/weekly-details.component').then(m => m.WeeklyDetailsComponent)
      },
      {
        path: 'recipe/:meal_id',
        loadComponent: () => import('./pages/weekly/recipe-details/recipe-details.component').then(m => m.RecipeDetailsComponent)
      },
      {
        path: 'recipes',
        loadComponent: () => import('./pages/recipes/recipes.component').then(m => m.RecipesComponent)
      },
      {
        path: 'settings',
        loadComponent: () => import('./pages/settings/settings.component').then(m => m.SettingsComponent)
      },
    ],
  },

  { path: '**', redirectTo: '' },
];
