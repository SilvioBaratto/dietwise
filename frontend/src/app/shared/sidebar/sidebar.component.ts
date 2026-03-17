import { Component, output, computed, inject, ChangeDetectionStrategy } from '@angular/core';
import { RouterModule, Router, NavigationEnd } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth.service';
import { toSignal } from '@angular/core/rxjs-interop';
import { filter, map, startWith } from 'rxjs';

interface NavLink {
  label: string
  path: string
  icon?: string
  description?: string
}

@Component({
  selector: 'app-sidebar',
  imports: [RouterModule, CommonModule],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SidebarComponent {
  // Services
  public auth = inject(AuthService);
  private router = inject(Router);

  // Outputs
  closeSidebar = output<void>();

  // Signals for reactive state - convert router events to signal
  private routerEvents = toSignal(
    this.router.events.pipe(
      filter((event): event is NavigationEnd => event instanceof NavigationEnd),
      map((event) => event.urlAfterRedirects || event.url),
      startWith(this.router.url)
    ),
    { initialValue: this.router.url }
  );

  currentRoute = computed(() => this.routerEvents());
  
  navLinks: NavLink[] = [
    {
      path: '/',
      label: 'Dashboard',
      description: 'Panoramica generale'
    },
    {
      path: '/weekly',
      label: 'Piani Settimanali',
      description: 'Gestisci le tue diete'
    },
    {
      path: '/recipes',
      label: 'Ricette',
      description: 'Le tue ricette salvate'
    },
    {
      path: '/settings',
      label: 'Impostazioni',
      description: 'Configura il profilo'
    },
  ]

  onLinkClick() {
    this.closeSidebar.emit();
  }

  // TrackBy function for optimal performance with *ngFor
  trackByPath(_index: number, item: NavLink): string {
    return item.path;
  }

  // Determine if exact matching should be used for a route
  isExactRoute(path: string): boolean {
    // Use exact matching for all routes except /weekly
    // - / (dashboard) is exact
    // - /weekly uses non-exact to match /weekly, /weekly/:diet_id, and /recipe/:meal_id
    // - /settings is exact
    return path !== '/weekly';
  }

  // Custom method to check if a link should be highlighted
  isLinkActive(path: string): boolean {
    const route = this.currentRoute();
    // Special case: highlight weekly when viewing recipe details
    if (path === '/weekly' && route.startsWith('/recipe/')) {
      return true;
    }
    // For other routes, let Angular's routerLinkActive handle it
    return false;
  }

  async onLogout(): Promise<void> {
    try {
      await this.auth.signOut();
      this.closeSidebar.emit(); // Close sidebar on mobile
      this.router.navigate(['/login']);
    } catch (err) {
      console.error('Logout error:', err);
    }
  }
}