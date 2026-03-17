import { Component, inject, signal, computed, ChangeDetectionStrategy } from '@angular/core';

import { Router, RouterOutlet, NavigationEnd } from '@angular/router';
import { SidebarComponent } from './shared/sidebar/sidebar.component';
import { LlmErrorToastComponent } from './shared/llm-error-toast/llm-error-toast.component';
import { AuthService } from './services/auth.service';
import { toSignal } from '@angular/core/rxjs-interop';
import { filter, map, startWith } from 'rxjs/operators';

@Component({
  selector: 'app-root',
  imports: [
    RouterOutlet,
    SidebarComponent,
    LlmErrorToastComponent,
],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    '(window:resize)': 'onResize()'
  }
})
export class AppComponent {
  // Services
  private auth = inject(AuthService);
  private router = inject(Router);

  // Signals for reactive state
  isAuthenticated = toSignal(this.auth.isAuthenticated$, { initialValue: false });
  sidebarOpen = signal(false);

  // Compute showLayout based on current route
  private currentRoute = toSignal(
    this.router.events.pipe(
      filter((event): event is NavigationEnd => event instanceof NavigationEnd),
      map((event) => {
        const url = event.url.split('?')[0].split('#')[0];
        return url;
      }),
      startWith(this.router.url.split('?')[0].split('#')[0])
    ),
    { initialValue: this.router.url.split('?')[0].split('#')[0] }
  );

  showLayout = computed(() => {
    const url = this.currentRoute();
    return !url.includes('/login') && !url.includes('/auth/callback');
  });

  constructor() {
    console.log('[AppComponent] Initialized. Current URL:', this.router.url);
  }

  toggleSidebar() {
    this.sidebarOpen.update(open => !open);
  }

  onSidebarLinkClick() {
    // if on mobile (below Tailwind's lg breakpoint of 1024px), close it
    if (window.innerWidth < 1024) {
      this.sidebarOpen.set(false);
    }
  }

  // Close sidebar on mobile when window is resized to desktop
  onResize() {
    if (window.innerWidth >= 1024) {
      // ensure sidebar closes on desktop since it's always visible
      this.sidebarOpen.set(false);
    }
  }
}