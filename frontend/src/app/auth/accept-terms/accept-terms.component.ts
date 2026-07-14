// src/app/auth/accept-terms/accept-terms.component.ts
import { Component, inject, signal, ChangeDetectionStrategy } from '@angular/core';
import { Router } from '@angular/router';
import { UserService } from '../../services/user.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-accept-terms',
  templateUrl: './accept-terms.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AcceptTermsComponent {
  private readonly userService = inject(UserService);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  hasScrolledToBottom = signal(false);
  scrollProgress = signal(0);
  submitting = signal(false);
  error = signal<string | null>(null);

  onTermsScroll(event: Event) {
    const element = event.target as HTMLElement;
    const scrollTop = element.scrollTop;
    const scrollHeight = element.scrollHeight - element.clientHeight;
    const progress = Math.min((scrollTop / scrollHeight) * 100, 100);
    this.scrollProgress.set(progress);

    const threshold = 50;
    const isAtBottom =
      element.scrollHeight - element.scrollTop - element.clientHeight < threshold;
    if (isAtBottom) {
      this.hasScrolledToBottom.set(true);
    }
  }

  acceptTerms() {
    if (!this.hasScrolledToBottom() || this.submitting()) {
      return;
    }
    this.submitting.set(true);
    this.error.set(null);
    this.userService.acceptTerms().subscribe({
      next: () => {
        this.router.navigateByUrl('/');
      },
      error: () => {
        this.submitting.set(false);
        this.error.set('Impossibile registrare l\'accettazione. Riprova.');
      },
    });
  }

  async logout(): Promise<void> {
    await this.auth.signOut();
    this.router.navigate(['/login']);
  }
}
