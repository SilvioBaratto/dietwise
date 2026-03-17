// src/app/auth/login/login.component.ts
import {
  Component,
  inject,
  computed,
  effect,
  signal,
  ChangeDetectionStrategy,
  ElementRef,
  viewChild,
} from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { DecimalPipe } from '@angular/common';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [],
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

  // Terms and conditions state
  showTermsModal = signal(false);
  hasScrolledToBottom = signal(false);
  hasAcceptedTerms = signal(false);
  scrollProgress = signal(0);
  canLogin = computed(() => this.hasAcceptedTerms());

  // View child for scroll container
  termsContent = viewChild<ElementRef>('termsContent');

  constructor() {
    // Use effect to handle auto-redirect when already authenticated
    effect(() => {
      if (this.isAuthenticated()) {
        const url = this.returnUrl();
        this.router.navigateByUrl(url);
      }
    });
  }

  openTermsModal() {
    this.showTermsModal.set(true);
    this.hasScrolledToBottom.set(false);
    this.scrollProgress.set(0);
    document.body.style.overflow = 'hidden';
  }

  closeTermsModal() {
    this.showTermsModal.set(false);
    document.body.style.overflow = '';
  }

  onTermsScroll(event: Event) {
    const element = event.target as HTMLElement;
    const scrollTop = element.scrollTop;
    const scrollHeight = element.scrollHeight - element.clientHeight;
    const progress = Math.min((scrollTop / scrollHeight) * 100, 100);
    this.scrollProgress.set(progress);

    const threshold = 50;
    const isAtBottom =
      element.scrollHeight - element.scrollTop - element.clientHeight <
      threshold;
    if (isAtBottom) {
      this.hasScrolledToBottom.set(true);
    }
  }

  acceptTerms() {
    if (this.hasScrolledToBottom()) {
      this.hasAcceptedTerms.set(true);
      this.closeTermsModal();
    }
  }

  async onLogin() {
    if (!this.canLogin()) {
      this.openTermsModal();
      return;
    }

    try {
      await this.auth.signInWithGoogle();
    } catch (err) {
      console.error(err);
    }
  }
}
