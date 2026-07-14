import { Component, ChangeDetectionStrategy, computed, inject } from '@angular/core';
import { NavigationEnd, Router, RouterLink, RouterLinkActive } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { filter, map } from 'rxjs';
import { NAV_ITEMS } from '../nav-item';
import { LucideLayoutDashboard, LucideCalendarDays, LucideBookOpen, LucideSettings } from '@lucide/angular';

@Component({
  selector: 'app-bottom-tab-bar',
  imports: [RouterLink, RouterLinkActive, LucideLayoutDashboard, LucideCalendarDays, LucideBookOpen, LucideSettings],
  templateUrl: './bottom-tab-bar.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { class: 'block md:hidden' },
})
export class BottomTabBarComponent {
  private readonly router = inject(Router);

  navItems = NAV_ITEMS;

  private readonly currentUrl = toSignal(
    this.router.events.pipe(
      filter((event): event is NavigationEnd => event instanceof NavigationEnd),
      map(() => this.router.url),
    ),
    { initialValue: this.router.url },
  );

  activeIndex = computed(() => {
    this.currentUrl();
    const index = this.navItems.findIndex((item) =>
      this.router.isActive(item.route, {
        paths: item.exact ? 'exact' : 'subset',
        queryParams: 'ignored',
        fragment: 'ignored',
        matrixParams: 'ignored',
      }),
    );
    return index === -1 ? null : index;
  });
}
