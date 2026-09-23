import { Routes } from '@angular/router';

import { ChatEmptyState } from './chat-empty-state/chat-empty-state';
import { ChatThread } from './chat-thread/chat-thread';
import { WorkersAiShell } from './workers-ai-shell/workers-ai-shell';

export const workersAiRoutes: Routes = [
  {
    path: '',
    component: WorkersAiShell,
    children: [
      { path: '', component: ChatEmptyState },
      { path: ':chatId', component: ChatThread },
    ],
  },
];
