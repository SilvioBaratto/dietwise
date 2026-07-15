import {
  Component,
  OnInit,
  signal,
  computed,
  inject,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
} from '@angular/core';

import { FormsModule } from '@angular/forms';
import { AsyncPipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Router, ActivatedRoute } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { forkJoin, catchError, of, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ApiKeyService } from '../../services/api-key.service';
import { AuthService } from '../../services/auth.service';
import { Provider } from '../../models/api-key.types';
import { UserSettingsIn, UserSettingsOut } from '../../models/user-settings.types';
import { PageHeaderComponent } from '../../shared/page-header/page-header.component';
import { ByokSettingsComponent } from './byok-settings/byok-settings.component';
import {
  LucideSettings,
  LucideInfo,
  LucideCheck,
  LucideAlertTriangle,
  LucideUser,
  LucideWeight,
  LucideRuler,
  LucideTarget,
  LucideSave,
  LucideLoader,
  LucideX,
  LucideLogOut,
} from '@lucide/angular';

@Component({
  selector: 'app-settings',
  imports: [
    FormsModule,
    AsyncPipe,
    PageHeaderComponent,
    ByokSettingsComponent,
    LucideSettings,
    LucideInfo,
    LucideCheck,
    LucideAlertTriangle,
    LucideUser,
    LucideWeight,
    LucideRuler,
    LucideTarget,
    LucideSave,
    LucideLoader,
    LucideX,
    LucideLogOut,
  ],
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SettingsComponent implements OnInit {
  private http = inject(HttpClient);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private cdr = inject(ChangeDetectorRef);
  private apiKeyService = inject(ApiKeyService);
  auth = inject(AuthService);

  // Form data (plain object for ngModel compatibility)
  settings: UserSettingsIn = {};

  // Signals for reactive state
  successMessage = signal('');
  errorMessage = signal('');
  isSavingSettings = signal(false);

  // Convert queryParams observable to signal
  private queryParams = toSignal(this.route.queryParams, {
    initialValue: {} as Record<string, string>,
  });
  isFirstTime = computed(() => this.queryParams()?.['firstTime'] === 'true');

  // BYOK: the active provider/model, two-way bound to <app-byok-settings>.
  // The child owns fetching/mutating provider config; this component only
  // needs the current values to include in its combined settings save.
  selectedProvider = signal<Provider>('openai');
  selectedModel = signal<string>('');
  byokReady = signal(false);

  // Page-level loading now covers only Personal/Additional Info — the BYOK
  // section renders unconditionally with its own internal skeleton so it can
  // resolve independently instead of waiting on this fetch.
  loading = signal(true);

  ngOnInit() {
    // Note: Authorization header is automatically added by authInterceptor
    this.http.get<UserSettingsOut>(`${environment.apiUrl}/settings/get_user_settings`).subscribe({
      next: (data) => {
        this.settings = {
          age: data.age,
          sex: data.sex,
          weight: data.weight,
          height: data.height,
          other_data: data.other_data,
          goals: data.goals,
        };

        // Trigger change detection for OnPush strategy
        this.cdr.markForCheck();
        this.loading.set(false);
      },
      error: (err) => {
        if (err.status !== 404) {
          console.error('Failed to load settings', err);
        }
        this.loading.set(false);
      },
    });
  }

  saveSettings() {
    if (this.isSavingSettings()) return;

    this.successMessage.set('');
    this.errorMessage.set('');
    this.isSavingSettings.set(true);

    // Note: Authorization header is automatically added by authInterceptor
    const settingsSave$ = this.http
      .post<UserSettingsOut>(`${environment.apiUrl}/settings/update_user_settings`, this.settings)
      .pipe(
        map(() => true),
        catchError((err) => {
          console.error('Save error', err);
          this.errorMessage.set('Errore nel salvataggio delle informazioni personali. Riprova.');
          return of(false);
        }),
      );

    const prefsSave$ = this.apiKeyService
      .updatePreferences(this.selectedProvider(), this.selectedModel())
      .pipe(
        map(() => true),
        catchError((err) => {
          this.errorMessage.set(err.error?.detail ?? 'Errore nel salvataggio delle preferenze AI.');
          return of(false);
        }),
      );

    forkJoin([settingsSave$, prefsSave$]).subscribe(([settingsOk, prefsOk]) => {
      this.isSavingSettings.set(false);
      if (!settingsOk || !prefsOk) return;

      if (this.isFirstTime()) {
        this.router.navigate(['/dashboard']);
      } else {
        this.successMessage.set('Impostazioni salvate.');
      }
    });
  }

  cancelSettings() {
    // Don't allow cancel if this is first-time setup
    if (this.isFirstTime()) {
      this.errorMessage.set('Devi completare la configurazione iniziale prima di procedere.');
      return;
    }
    // Navigate back to dashboard without saving
    this.router.navigate(['/dashboard']);
  }

  async onLogout(): Promise<void> {
    try {
      await this.auth.signOut();
      this.router.navigate(['/login']);
    } catch (err) {
      console.error('Logout error:', err);
    }
  }
}
