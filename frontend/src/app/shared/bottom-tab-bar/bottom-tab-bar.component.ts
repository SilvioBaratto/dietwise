import { Component, ChangeDetectionStrategy } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
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
  navItems = NAV_ITEMS;
}
