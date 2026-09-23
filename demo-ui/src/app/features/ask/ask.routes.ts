import { Routes } from '@angular/router';

import { AskPage } from './ask-page/ask-page';
import { AskStore } from './ask.store';

export const askRoutes: Routes = [
  {
    path: '',
    component: AskPage,
    // Provided on the route so its lifecycle matches the /ask page, same idea
    // as TodosStore/TodosShell.
    providers: [AskStore],
  },
];
