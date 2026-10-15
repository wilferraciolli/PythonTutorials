import { Routes } from '@angular/router';

import { MySettingsPage } from './my-settings-page/my-settings-page';
import { SystemSettingsPage } from './system-settings-page/system-settings-page';

export const settingsRoutes: Routes = [
  { path: '', component: MySettingsPage },
  { path: 'system', component: SystemSettingsPage },
];
