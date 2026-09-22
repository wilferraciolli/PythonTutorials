import { Routes } from '@angular/router';

import { ProfileEditPage } from './profile-edit-page/profile-edit-page';
import { ProfilePage } from './profile-page/profile-page';

export const profileRoutes: Routes = [
  { path: '', component: ProfilePage },
  { path: 'edit', component: ProfileEditPage },
];
