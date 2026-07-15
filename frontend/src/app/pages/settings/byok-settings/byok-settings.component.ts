import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  effect,
  inject,
  model,
  output,
  signal,
} from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { toSignal } from '@angular/core/rxjs-interop';
import { forkJoin } from 'rxjs';
import { ApiKeyService } from '../../../services/api-key.service';
import { ApiKeyResponse, Preferences, Provider, ProviderInfo } from '../../../models/api-key.types';
import { EditableSelectComponent } from '../../../shared/editable-select/editable-select.component';
import {
  LucideAlertTriangle,
  LucideCheck,
  LucideInfo,
  LucideLoader,
  LucidePencil,
  LucidePlus,
  LucideTrash2,
} from '@lucide/angular';

@Component({
  selector: 'app-byok-settings',
  imports: [
    ReactiveFormsModule,
    EditableSelectComponent,
    LucideAlertTriangle,
    LucideCheck,
    LucideInfo,
    LucideLoader,
    LucidePencil,
    LucidePlus,
    LucideTrash2,
  ],
  templateUrl: './byok-settings.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ByokSettingsComponent implements OnInit {
  private apiKeyService = inject(ApiKeyService);

  // Two-way bound to the parent: which provider/model is "active" for
  // diet generation. Parent's saveSettings() persists this via
  // apiKeyService.updatePreferences() alongside the rest of the form.
  selectedProvider = model<Provider>('openai');
  selectedModel = model<string>('');

  // Fires once this component's own initial fetch resolves, so the parent
  // can gate its Save button until real preferences have loaded (instead of
  // submitting the model()'s default '' / 'openai' placeholder values).
  loaded = output<void>();

  providers = signal<ProviderInfo[]>([]);
  savedKeys = signal<ApiKeyResponse[]>([]);
  loading = signal(true);
  loadError = signal('');

  isSaving = signal(false);
  isValidating = signal(false);
  isDeletingProvider = signal<Provider | null>(null);
  keyError = signal('');
  keySuccess = signal('');
  showKeyInput = signal(false);

  byokForm = new FormGroup({
    formProvider: new FormControl<Provider>('openai', { nonNullable: true }),
    apiKey: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, Validators.minLength(10)],
    }),
    baseUrl: new FormControl('', { nonNullable: true }),
    apiVersion: new FormControl('', { nonNullable: true }),
  });

  providersMap = computed(() => new Map(this.providers().map((p) => [p.slug, p])));

  providerGroups = computed(() => {
    const all = this.providers();
    return [
      { title: 'Provider Cloud', items: all.filter((p) => !p.requires_base_url) },
      {
        title: 'Endpoint Personalizzati / Self-hosted',
        items: all.filter((p) => p.requires_base_url),
      },
    ];
  });

  activeProviderInfo = computed(() => this.providersMap().get(this.selectedProvider()));

  private formProviderSignal = toSignal(this.byokForm.controls.formProvider.valueChanges, {
    initialValue: this.byokForm.controls.formProvider.value,
  });
  selectedFormProviderInfo = computed(() => this.providersMap().get(this.formProviderSignal()));

  baseUrlPlaceholder = computed(() => {
    switch (this.selectedFormProviderInfo()?.slug) {
      case 'ollama':
        return 'https://il-tuo-tunnel-pubblico.example.com/v1 (non localhost)';
      case 'azure_openai':
        return 'https://<risorsa>.openai.azure.com/openai/deployments/<deployment>';
      case 'microsoft_foundry':
        return 'https://<progetto>.services.ai.azure.com/openai/v1/';
      case 'openai_generic':
        return 'https://api.tuo-endpoint.com/v1';
      default:
        return '';
    }
  });

  constructor() {
    effect(() => this.applyDynamicValidators(this.selectedFormProviderInfo()));
  }

  ngOnInit(): void {
    forkJoin({
      keys: this.apiKeyService.getKeys(),
      providersRes: this.apiKeyService.getProviders(),
      prefs: this.apiKeyService.getPreferences(),
    }).subscribe({
      next: ({ keys, providersRes, prefs }) => {
        this.savedKeys.set(keys);
        this.providers.set(providersRes.providers);
        this.applyInitialPreferences(providersRes.providers, prefs);
        this.loading.set(false);
        this.loaded.emit();
      },
      error: () => {
        this.loadError.set('Impossibile caricare la configurazione dei provider AI');
        this.loading.set(false);
        this.loaded.emit();
      },
    });
  }

  private applyInitialPreferences(list: ProviderInfo[], prefs: Preferences): void {
    const provider = (prefs.provider as Provider) ?? list[0]?.slug ?? 'openai';
    this.selectedProvider.set(provider);
    const info = list.find((p) => p.slug === provider);
    const curated = info?.models ?? [];
    const saved = prefs.model;
    // Free-form providers (Azure/Foundry/generic/Ollama) have no fixed
    // catalog to validate membership against — trust the saved value as-is
    // rather than discarding a valid custom deployment name.
    const savedIsUsable = !!saved && (info?.free_form_models || curated.includes(saved));
    this.selectedModel.set(savedIsUsable ? saved! : (info?.default_model ?? curated[0] ?? ''));
  }

  private applyDynamicValidators(info: ProviderInfo | undefined): void {
    const { apiKey, baseUrl, apiVersion } = this.byokForm.controls;

    apiKey.setValidators(
      info?.requires_api_key === false ? [] : [Validators.required, Validators.minLength(10)],
    );
    baseUrl.setValidators(info?.requires_base_url ? [Validators.required] : []);
    apiVersion.setValidators(info?.requires_api_version ? [Validators.required] : []);

    // reset() (not setValue()) also clears touched/dirty state — switching
    // to a provider that doesn't need this field shouldn't leave behind a
    // stale validation message next time it becomes relevant.
    if (!info?.requires_base_url) baseUrl.reset('', { emitEvent: false });
    if (!info?.requires_api_version) apiVersion.reset('', { emitEvent: false });

    apiKey.updateValueAndValidity({ emitEvent: false });
    baseUrl.updateValueAndValidity({ emitEvent: false });
    apiVersion.updateValueAndValidity({ emitEvent: false });
  }

  getKeyForProvider(provider: Provider): ApiKeyResponse | undefined {
    return this.savedKeys().find((k) => k.provider === provider);
  }

  labelFor(provider: Provider): string {
    return this.providersMap().get(provider)?.label ?? provider;
  }

  private reloadKeys(): void {
    this.apiKeyService.getKeys().subscribe({
      next: (keys) => this.savedKeys.set(keys),
      error: () => this.keyError.set('Impossibile ricaricare le chiavi API'),
    });
  }

  onProviderChange(provider: Provider): void {
    this.selectedProvider.set(provider);
    const info = this.providersMap().get(provider);
    this.selectedModel.set(info?.default_model ?? info?.models[0] ?? '');
  }

  validateAndSave(): void {
    if (this.byokForm.invalid || this.isSaving() || this.isValidating()) return;

    this.keyError.set('');
    this.keySuccess.set('');

    const { formProvider, apiKey, baseUrl, apiVersion } = this.byokForm.controls;
    const provider = formProvider.value;
    const key = apiKey.value;
    const options = {
      baseUrl: baseUrl.value || undefined,
      apiVersion: apiVersion.value || undefined,
    };

    this.isValidating.set(true);

    this.apiKeyService.validateKey(provider, key, options).subscribe({
      next: (result) => {
        this.isValidating.set(false);

        if (!result.is_valid) {
          this.keyError.set(result.error ?? 'Chiave non valida');
          return;
        }

        this.isSaving.set(true);
        this.apiKeyService.saveKey(provider, key, options).subscribe({
          next: () => {
            this.byokForm.controls.apiKey.reset('');
            this.showKeyInput.set(false);
            this.isSaving.set(false);
            this.keySuccess.set(`Chiave ${this.labelFor(provider)} salvata con successo`);
            this.reloadKeys();
          },
          error: (err) => {
            this.isSaving.set(false);
            this.keyError.set(
              err.error?.error?.message ??
                err.error?.detail ??
                'Errore nel salvataggio della chiave',
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
        this.keySuccess.set(`Chiave ${this.labelFor(provider)} rimossa`);
        this.reloadKeys();
      },
      error: (err) => {
        this.isDeletingProvider.set(null);
        this.keyError.set(
          err.error?.error?.message ?? err.error?.detail ?? 'Impossibile eliminare la chiave',
        );
      },
    });
  }

  onChangeKeyFor(provider: Provider): void {
    const existing = this.getKeyForProvider(provider);
    this.byokForm.controls.formProvider.setValue(provider);
    this.byokForm.controls.apiKey.reset('');
    this.byokForm.controls.baseUrl.reset(existing?.base_url ?? '');
    this.byokForm.controls.apiVersion.reset(existing?.api_version ?? '');
    this.showKeyInput.set(true);
    this.keyError.set('');
    this.keySuccess.set('');
  }
}
