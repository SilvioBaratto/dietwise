import { Component, OnInit, signal, computed, inject, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';

import { FormsModule, ReactiveFormsModule, FormGroup, FormControl, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router, ActivatedRoute } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { forkJoin } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ApiKeyService } from '../../services/api-key.service';
import { ApiKeyResponse, AvailableModels, Provider } from '../../models/api-key.types';
import { CostBadgeComponent } from '../../shared/cost-badge/cost-badge.component';

interface UserSettingsIn {
  age?: number;
  sex?: string;
  weight?: number;
  height?: number;
  other_data?: string;
  goals?: string;
}
interface UserSettingsOut extends UserSettingsIn {
  id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

@Component({
  selector: 'app-settings',
  imports: [FormsModule, ReactiveFormsModule, CostBadgeComponent],
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

  // Form data (plain object for ngModel compatibility)
  settings: UserSettingsIn = {};

  // Signals for reactive state
  successMessage = signal('');
  errorMessage = signal('');

  // Convert queryParams observable to signal
  private queryParams = toSignal(this.route.queryParams, { initialValue: {} as Record<string, string> });
  isFirstTime = computed(() => this.queryParams()?.['firstTime'] === 'true');

  // Weight and height as signals for reactive BMI calculation
  private weight = signal<number | undefined>(undefined);
  private height = signal<number | undefined>(undefined);

  // Computed signals for BMI calculations
  bmi = computed(() => {
    const w = this.weight();
    const h = this.height();

    if (w && h) {
      const heightInMeters = h / 100;
      const bmiValue = w / (heightInMeters * heightInMeters);
      return parseFloat(bmiValue.toFixed(1));
    }
    return 0;
  });

  bmiDisplay = computed(() => {
    const bmiValue = this.bmi();
    return bmiValue === 0 ? '0' : bmiValue.toFixed(1);
  });

  bmiCategory = computed(() => {
    const bmiValue = this.bmi();

    if (bmiValue === 0) {
      return '';
    } else if (bmiValue < 18.5) {
      return 'Sottopeso';
    } else if (bmiValue < 25) {
      return 'Normopeso';
    } else if (bmiValue < 30) {
      return 'Sovrappeso';
    } else if (bmiValue < 35) {
      return 'Obesità Classe I';
    } else if (bmiValue < 40) {
      return 'Obesità Classe II';
    } else {
      return 'Obesità Classe III';
    }
  });

  // Watchers to sync form changes with signal-based BMI calculation
  updateWeightSignal() {
    this.weight.set(this.settings.weight);
  }

  updateHeightSignal() {
    this.height.set(this.settings.height);
  }

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

          // Initialize weight and height signals for BMI calculation
          this.weight.set(data.weight);
          this.height.set(data.height);

          // Trigger change detection for OnPush strategy
          this.cdr.markForCheck();
        },
        error: (err) => {
          if (err.status !== 404) {
            console.error('Failed to load settings', err);
          }
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
  getBMI(): string {
    return this.bmiDisplay();
  }

  getBMICategory(): string {
    return this.bmiCategory();
  }

  // --- BYOK Methods ---

  loadApiKeys(): void {
    this.apiKeyService.getKeys().subscribe({
      next: (keys) => this.savedKeys.set(keys),
      error: (err) => {
        if (err.status !== 404) {
          this.keyError.set('Impossibile caricare le chiavi API');
        }
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
      },
      error: () => this.prefsError.set('Impossibile caricare le preferenze AI'),
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
}
