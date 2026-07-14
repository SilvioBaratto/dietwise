// src/app/auth/login/login.component.ts
import {
  Component,
  inject,
  computed,
  effect,
  ChangeDetectionStrategy,
} from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { AuthService } from '../../services/auth.service';
import { LucideArrowRight, LucideCheck } from '@lucide/angular';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [LucideArrowRight, LucideCheck],
})
export class LoginComponent {
  // Services
  private auth = inject(AuthService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  // Signals for reactive state
  private queryParams = toSignal(this.route.queryParams, {
    initialValue: {} as Record<string, string>,
  });
  returnUrl = computed(() => this.queryParams()?.['returnUrl'] || '/');

  // Convert isAuthenticated$ observable to signal
  isAuthenticated = toSignal(this.auth.isAuthenticated$, {
    initialValue: false,
  });

  constructor() {
    // Use effect to handle auto-redirect when already authenticated
    effect(() => {
      if (this.isAuthenticated()) {
        const url = this.returnUrl();
        this.router.navigateByUrl(url);
      }
    });
  }

  // Terms & Conditions acceptance is gated server-side, post-login (see
  // AcceptTermsComponent) - not here, so a browser refresh or new device
  // never has to re-litigate something the account already recorded.
  async onLogin() {
    try {
      await this.auth.signInWithGoogle();
    } catch (err) {
      console.error(err);
    }
  }
}
