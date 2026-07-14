import { Component, computed, inject, ChangeDetectionStrategy } from '@angular/core';
import { RouterModule, Router, NavigationEnd } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth.service';
import { NAV_ITEMS } from '../nav-item';
import { toSignal } from '@angular/core/rxjs-interop';
import { filter, map, startWith } from 'rxjs';
import {
  LucideLayoutDashboard,
  LucideCalendarDays,
  LucideBookOpen,
  LucideSettings,
  LucideChevronRight,
  LucideLogOut,
} from '@lucide/angular';

@Component({
  selector: 'app-sidebar',
  imports: [
    RouterModule,
    CommonModule,
    LucideLayoutDashboard,
    LucideCalendarDays,
    LucideBookOpen,
    LucideSettings,
    LucideChevronRight,
    LucideLogOut,
  ],
  templateUrl: './sidebar.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SidebarComponent {
  // Services
  public auth = inject(AuthService);
  private router = inject(Router);

  navItems = NAV_ITEMS;

  // Signals for reactive state - convert router events to signal
  private routerEvents = toSignal(
    this.router.events.pipe(
      filter((event): event is NavigationEnd => event instanceof NavigationEnd),
      map(event => event.urlAfterRedirects || event.url),
      startWith(this.router.url)
    ),
    { initialValue: this.router.url }
  );

  currentRoute = computed(() => this.routerEvents());

  // Custom method to check if a link should be highlighted
  // Special case: highlight weekly when viewing recipe details
  isLinkActive(route: string): boolean {
    if (route === '/weekly' && this.currentRoute().startsWith('/recipe/')) {
      return true;
    }
    return false;
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
