import { Component, OnInit, signal, computed, inject, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router, ActivatedRoute } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

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
  imports: [CommonModule, FormsModule],
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SettingsComponent implements OnInit {
  private http = inject(HttpClient);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private cdr = inject(ChangeDetectorRef);

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
}
