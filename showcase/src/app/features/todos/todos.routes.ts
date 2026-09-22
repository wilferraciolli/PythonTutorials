import { Routes } from '@angular/router';

import { TodoForm } from './todo-form/todo-form';
import { TodosList } from './todos-list/todos-list';
import { TodosShell } from './todos-shell/todos-shell';

export const todosRoutes: Routes = [
  {
    path: '',
    component: TodosShell,
    children: [
      { path: '', component: TodosList },
      { path: 'new', component: TodoForm },
      { path: ':id/edit', component: TodoForm },
    ],
  },
];
