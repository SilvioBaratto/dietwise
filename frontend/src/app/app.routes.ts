// src/app/app.routes.ts

import { Routes } from '@angular/router';
import { AuthGuard } from './guard/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
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
    path: '',
    canActivate: [AuthGuard],
    children: [
      {
        path: '',
        loadComponent: () => import('./components/dashboard/dashboard.component').then(m => m.DashboardComponent)
      },
      {
        path: 'weekly',
        loadComponent: () => import('./components/weekly/weekly.component').then(m => m.WeeklyComponent)
      },
      {
        path: 'weekly/:diet_id',
        loadComponent: () => import('./components/weekly/weekly-details/weekly-details.component').then(m => m.WeeklyDetailsComponent)
      },
      {
        path: 'recipe/:meal_id',
        loadComponent: () => import('./components/weekly/recipe-details/recipe-details.component').then(m => m.RecipeDetailsComponent)
      },
      {
        path: 'recipes',
        loadComponent: () => import('./components/recipes/recipes.component').then(m => m.RecipesComponent)
      },
      {
        path: 'settings',
        loadComponent: () => import('./components/settings/settings.component').then(m => m.SettingsComponent)
      },
    ],
  },

  { path: '**', redirectTo: '' },
];
