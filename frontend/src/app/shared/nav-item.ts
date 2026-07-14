export type NavIconKey = 'dashboard' | 'weekly' | 'recipes' | 'settings';

export interface NavItem {
  route: string;
  exact: boolean;
  icon: NavIconKey;
  sidebarLabel: string;
  mobileLabel: string;
}

export const NAV_ITEMS: NavItem[] = [
  { route: '/', exact: true, icon: 'dashboard', sidebarLabel: 'Dashboard', mobileLabel: 'Home' },
  { route: '/weekly', exact: false, icon: 'weekly', sidebarLabel: 'Piani Settimanali', mobileLabel: 'Piani' },
  { route: '/recipes', exact: true, icon: 'recipes', sidebarLabel: 'Ricette', mobileLabel: 'Ricette' },
  { route: '/settings', exact: true, icon: 'settings', sidebarLabel: 'Impostazioni', mobileLabel: 'Profilo' },
];
