import { Component, OnInit, signal, computed, inject, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';

import { FormsModule, ReactiveFormsModule, FormGroup, FormControl, Validators } from '@angular/forms';
import { AsyncPipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Router, ActivatedRoute } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { forkJoin } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ApiKeyService } from '../../services/api-key.service';
import { AuthService } from '../../services/auth.service';
import { ApiKeyResponse, AvailableModels, Provider } from '../../models/api-key.types';
import { UserSettingsIn, UserSettingsOut } from '../../models/user-settings.types';
import { PageHeaderComponent } from '../../shared/page-header/page-header.component';
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
  LucidePlus,
  LucideX,
  LucideLogOut,
} from '@lucide/angular';

@Component({
  selector: 'app-settings',
  imports: [
    FormsModule,
    ReactiveFormsModule,
    AsyncPipe,
    PageHeaderComponent,
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
    LucidePlus,
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

  // Convert queryParams observable to signal
  private queryParams = toSignal(this.route.queryParams, { initialValue: {} as Record<string, string> });
  isFirstTime = computed(() => this.queryParams()?.['firstTime'] === 'true');

  // BYOK state
  savedKeys = signal<ApiKeyResponse[]>([]);
  availableModels = signal<AvailableModels>({ openai: [], google: [], anthropic: [] });
  selectedProvider = signal<Provider>('openai');
  selectedModel = signal<string>('');
  isSaving = signal(false);
  isValidating = signal(false);
  isDeletingProvider = signal<Provider | null>(null);
  keyError = signal('');
  keySuccess = signal('');
  prefsError = signal('');
  showKeyInput = signal(false);

  providers: Provider[] = ['openai', 'google', 'anthropic'];
  providerLabels: Record<Provider, string> = {
    openai: 'OpenAI',
    google: 'Google Gemini',
    anthropic: 'Anthropic',
  };

  byokForm = new FormGroup({
    formProvider: new FormControl<Provider>('openai', { nonNullable: true }),
    apiKey: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, Validators.minLength(10)],
    }),
  });

  modelsForProvider = computed(() => {
    const models = this.availableModels();
    const provider = this.selectedProvider();
    return models[provider] ?? [];
  });

  getKeyForProvider(provider: Provider): ApiKeyResponse | undefined {
    return this.savedKeys().find(k => k.provider === provider);
  }

  // Page-level loading, gated on all three initial fetches below
  loading = signal(true);
  private settingsLoaded = false;
  private apiKeysLoaded = false;
  private modelsLoaded = false;

  private markLoaded(which: 'settings' | 'apiKeys' | 'models'): void {
    if (which === 'settings') this.settingsLoaded = true;
    if (which === 'apiKeys') this.apiKeysLoaded = true;
    if (which === 'models') this.modelsLoaded = true;
    if (this.settingsLoaded && this.apiKeysLoaded && this.modelsLoaded) {
      this.loading.set(false);
    }
  }

  ngOnInit() {
    // Note: Authorization header is automatically added by authInterceptor
    this.http
      .get<UserSettingsOut>(
        `${environment.apiUrl}/settings/get_user_settings`
      )
      .subscribe({
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
          this.markLoaded('settings');
        },
        error: (err) => {
          if (err.status !== 404) {
            console.error('Failed to load settings', err);
          }
          this.markLoaded('settings');
        },
      });

    this.loadApiKeys();
    this.loadModelsAndPreferences();
  }

  saveSettings() {
    this.successMessage.set('');
    this.errorMessage.set('');

    // Note: Authorization header is automatically added by authInterceptor
    this.http
      .post<UserSettingsOut>(
        `${environment.apiUrl}/settings/update_user_settings`,
        this.settings
      )
      .subscribe({
        next: () => {
          // Redirect to the dashboard on successful save
          this.router.navigate(['/dashboard']);
        },
        error: (err) => {
          console.error('Save error', err);
          this.errorMessage.set('Errore nel salvataggio. Riprova.');
        },
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

  // Expose computed signals to template
  // --- BYOK Methods ---

  loadApiKeys(): void {
    this.apiKeyService.getKeys().subscribe({
      next: (keys) => {
        this.savedKeys.set(keys);
        this.markLoaded('apiKeys');
      },
      error: (err) => {
        if (err.status !== 404) {
          this.keyError.set('Impossibile caricare le chiavi API');
        }
        this.markLoaded('apiKeys');
      },
    });
  }

  loadModelsAndPreferences(): void {
    forkJoin({
      models: this.apiKeyService.getAvailableModels(),
      prefs: this.apiKeyService.getPreferences(),
    }).subscribe({
      next: ({ models, prefs }) => {
        this.availableModels.set(models);
        const provider = (prefs.provider as Provider) ?? 'openai';
        this.selectedProvider.set(provider);
        this.selectedModel.set(prefs.model ?? models[provider]?.[0] ?? '');
        this.markLoaded('models');
      },
      error: () => {
        this.prefsError.set('Impossibile caricare le preferenze AI');
        this.markLoaded('models');
      },
    });
  }

  validateAndSave(): void {
    if (this.byokForm.invalid || this.isSaving() || this.isValidating()) return;

    this.keyError.set('');
    this.keySuccess.set('');

    const provider = this.byokForm.controls.formProvider.value;
    const apiKey = this.byokForm.controls.apiKey.value;

    this.isValidating.set(true);

    this.apiKeyService.validateKey(provider, apiKey).subscribe({
      next: (result) => {
        this.isValidating.set(false);

        if (!result.is_valid) {
          this.keyError.set(result.error ?? 'Chiave non valida');
          return;
        }

        this.isSaving.set(true);
        this.apiKeyService.saveKey(provider, apiKey).subscribe({
          next: () => {
            this.byokForm.controls.apiKey.reset();
            this.showKeyInput.set(false);
            this.isSaving.set(false);
            this.keySuccess.set(`Chiave ${this.providerLabels[provider]} salvata con successo`);
            this.loadApiKeys();
          },
          error: (err) => {
            this.isSaving.set(false);
            this.keyError.set(
              err.error?.error?.message ?? err.error?.detail ?? 'Errore nel salvataggio della chiave'
            );
          },
        });
      },
      error: (err) => {
        this.isValidating.set(false);
        this.keyError.set(err.error?.detail ?? 'Errore durante la validazione');
      },
    });
  }

  deleteKey(provider: Provider): void {
    this.keyError.set('');
    this.keySuccess.set('');
    this.isDeletingProvider.set(provider);

    this.apiKeyService.deleteKey(provider).subscribe({
      next: () => {
        this.isDeletingProvider.set(null);
        this.keySuccess.set(`Chiave ${this.providerLabels[provider]} rimossa`);
        this.loadApiKeys();
      },
      error: (err) => {
        this.isDeletingProvider.set(null);
        this.keyError.set(
          err.error?.error?.message ?? err.error?.detail ?? 'Impossibile eliminare la chiave'
        );
      },
    });
  }

  updatePreferences(): void {
    this.prefsError.set('');

    this.apiKeyService.updatePreferences(this.selectedProvider(), this.selectedModel()).subscribe({
      next: () => this.keySuccess.set('Preferenze AI salvate'),
      error: (err) => {
        this.prefsError.set(err.error?.detail ?? 'Errore nel salvataggio delle preferenze');
      },
    });
  }

  onChangeKeyFor(provider: Provider): void {
    this.byokForm.controls.formProvider.setValue(provider);
    this.byokForm.controls.apiKey.reset();
    this.showKeyInput.set(true);
    this.keyError.set('');
    this.keySuccess.set('');
  }

  onProviderChange(provider: Provider): void {
    this.selectedProvider.set(provider);
    const models = this.availableModels()[provider];
    this.selectedModel.set(models?.[0] ?? '');
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
