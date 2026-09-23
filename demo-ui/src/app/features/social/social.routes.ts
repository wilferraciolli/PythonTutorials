import { Routes } from '@angular/router';

import { GroupPage } from './group-page/group-page';
import { GroupsPage } from './groups-page/groups-page';
import { PostPage } from './post-page/post-page';

// Mounted at /groups (app.routes.ts). The timeline has its own top-level route.
export const groupsRoutes: Routes = [
  { path: '', component: GroupsPage },
  { path: ':groupId', component: GroupPage },
  { path: ':groupId/posts/:postId', component: PostPage },
];
