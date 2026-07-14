import { Component, computed, inject, effect, signal, viewChild, viewChildren, ElementRef, ChangeDetectionStrategy } from '@angular/core';
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

  activeIndex = computed(() => {
    const route = this.currentRoute();
    const index = this.navItems.findIndex((item) => this.isLinkActive(item.route) ||
      this.router.isActive(item.route, {
        paths: item.exact ? 'exact' : 'subset',
        queryParams: 'ignored',
        fragment: 'ignored',
        matrixParams: 'ignored',
      }));
    void route; // recompute when the route changes
    return index === -1 ? null : index;
  });

  // Position of the sliding active-indicator circle, measured from the
  // rendered icon (relative to the nav container's own bounding box, not
  // offsetParent — the nav rows are themselves positioned for z-index
  // stacking, which would otherwise throw off plain offsetTop/offsetLeft).
  private readonly navRef = viewChild<ElementRef<HTMLElement>>('navEl');
  private readonly iconRefs = viewChildren<ElementRef<HTMLElement>>('navIcon');
  indicatorTop = signal(0);
  indicatorLeft = signal(0);

  constructor() {
    effect(() => {
      const index = this.activeIndex();
      const icons = this.iconRefs();
      const nav = this.navRef()?.nativeElement;
      if (index === null || !icons[index] || !nav) return;
      const iconRect = icons[index].nativeElement.getBoundingClientRect();
      const navRect = nav.getBoundingClientRect();
      this.indicatorTop.set(iconRect.top - navRect.top + iconRect.height / 2);
      this.indicatorLeft.set(iconRect.left - navRect.left + iconRect.width / 2);
    });
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
