import { Component, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatTableModule } from '@angular/material/table';
import { RouterLink } from '@angular/router';
import { TranslocoPipe } from '@jsverse/transloco';
import { LinkService } from '@wiliamferraciolli/ngx-api-client';
import { firstValueFrom } from 'rxjs';

import { I18nService } from '../../../core/i18n/i18n.service';
import { TranslationService } from '../../../core/i18n/translation.service';
import { ConfirmDialog } from '../../../shared/confirm-dialog/confirm-dialog';
import { Todo, TodoState, TodosStore } from '../todos.store';

@Component({
  selector: 'app-todos-list',
  imports: [
    DatePipe,
    RouterLink,
    MatButtonModule,
    MatChipsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatTableModule,
    TranslocoPipe,
  ],
  templateUrl: './todos-list.html',
  styleUrl: './todos-list.scss',
})
export class TodosList {
  protected readonly store = inject(TodosStore);
  protected readonly links = inject(LinkService);
  private readonly dialog = inject(MatDialog);
  private readonly i18n = inject(TranslationService);
  // Dates follow the user's locale setting.
  protected readonly preferences = inject(I18nService);

  protected readonly displayedColumns = ['title', 'state', 'complete_by', 'actions'];

  protected setStateFilter(value: string): void {
    this.store.stateFilter.set(value === '' ? null : (value as TodoState));
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
            title: this.i18n.t('todos.list.deleteDialog.title'),
            message: this.i18n.t('todos.list.deleteDialog.message', { name: todo.title }),
            confirmLabel: this.i18n.t('common.delete'),
            cancelLabel: this.i18n.t('common.cancel'),
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
