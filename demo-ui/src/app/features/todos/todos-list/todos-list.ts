import { Component, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { RouterLink } from '@angular/router';
import { LinkService } from '@wiliamferraciolli/ngx-api-client';
import { firstValueFrom } from 'rxjs';

import { ConfirmDialog } from '../../../shared/confirm-dialog/confirm-dialog';
import { Todo, TodoState, TodosStore } from '../todos.store';

@Component({
  selector: 'app-todos-list',
  imports: [
    DatePipe,
    RouterLink,
    MatButtonModule,
    MatButtonToggleModule,
    MatDialogModule,
    MatIconModule,
  ],
  templateUrl: './todos-list.html',
  styleUrl: './todos-list.scss',
})
export class TodosList {
  protected readonly store = inject(TodosStore);
  protected readonly links = inject(LinkService);
  private readonly dialog = inject(MatDialog);

  protected setStateFilter(value: string): void {
    this.store.stateFilter.set(value === '' ? null : (value as TodoState));
  }

  // The API's own wording for a state ("Active"), falling back to the raw
  // value until its metadata has loaded.
  protected stateLabel(state: TodoState): string {
    return this.store.stateOptions().find((option) => option.value === state)?.viewValue ?? state;
  }

  // Past its due date and still open.
  protected isOverdue(todo: Todo): boolean {
    return todo.state !== 'CLOSED' && new Date(todo.complete_by).getTime() < Date.now();
  }

  protected canToggleClosed(todo: Todo): boolean {
    return this.links.hasLink(todo.links['update']);
  }

  // Follows the todo's own `update` link with just `state` flipped —
  // there's no dedicated "close" link in the API, so a full update is how
  // the UI is meant to change it (see todos.store.ts.updateTodo).
  protected async toggleClosed(todo: Todo): Promise<void> {
    const nextState: TodoState = todo.state === 'CLOSED' ? 'NEW' : 'CLOSED';
    await this.store.updateTodo(todo, {
      title: todo.title,
      description: todo.description,
      complete_by: todo.complete_by,
      state: nextState,
    });
  }

  protected async deleteTodo(todo: Todo): Promise<void> {
    const confirmed = await firstValueFrom(
      this.dialog
        .open(ConfirmDialog, {
          data: {
            title: 'Delete todo',
            message: `Delete "${todo.title}"? This can't be undone.`,
            confirmLabel: 'Delete',
            tone: 'danger',
          },
        })
        .afterClosed(),
    );

    if (confirmed) {
      await this.store.deleteTodo(todo);
    }
  }
}
