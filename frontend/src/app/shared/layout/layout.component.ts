import { Component, ElementRef, inject, signal, ChangeDetectionStrategy, viewChild, effect } from '@angular/core';
import { Router, RouterOutlet, NavigationEnd } from '@angular/router';
import { Title } from '@angular/platform-browser';
import { SidebarComponent } from '../sidebar/sidebar.component';
import { LlmErrorToastComponent } from '../llm-error-toast/llm-error-toast.component';
import { NAV_ITEMS } from '../nav-item';
import { toSignal } from '@angular/core/rxjs-interop';
import { filter, map, startWith } from 'rxjs/operators';
import { LucideMenu } from '@lucide/angular';

@Component({
  selector: 'app-layout',
  imports: [RouterOutlet, SidebarComponent, LlmErrorToastComponent, LucideMenu],
  templateUrl: './layout.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    '(window:resize)': 'onResize()',
  },
})
export class LayoutComponent {
  private router = inject(Router);
  private title = inject(Title);

  mainContent = viewChild<ElementRef<HTMLElement>>('mainContent');

  sidebarOpen = signal(false);

  private currentPageLabel = toSignal(
    this.router.events.pipe(
      filter((event): event is NavigationEnd => event instanceof NavigationEnd),
      map(event => this.labelForUrl(event.urlAfterRedirects)),
      startWith(this.labelForUrl(this.router.url))
    ),
    { initialValue: this.labelForUrl(this.router.url) }
  );

  routeAnnouncement = this.currentPageLabel;

  constructor() {
    effect(() => {
      const pageLabel = this.currentPageLabel();
      this.title.setTitle(`${pageLabel} — DietologoAI`);
      this.mainContent()?.nativeElement.focus();
    });
  }

  private labelForUrl(url: string): string {
    const path = url.split('?')[0].split('#')[0];
    const match = NAV_ITEMS.find(item =>
      item.exact ? path === item.route : path === item.route || path.startsWith(item.route + '/')
    );
    return match?.sidebarLabel ?? 'DietologoAI';
  }

  toggleSidebar() {
    this.sidebarOpen.update(open => !open);
  }

  onSidebarLinkClick() {
    if (window.innerWidth < 1024) {
      this.sidebarOpen.set(false);
    }
  }

  onResize() {
    if (window.innerWidth >= 1024) {
      this.sidebarOpen.set(false);
    }
  }
}
