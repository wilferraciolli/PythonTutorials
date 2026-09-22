import { Component, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatTableModule } from '@angular/material/table';
import { firstValueFrom } from 'rxjs';

import { ConfirmDialog } from '../../../shared/confirm-dialog/confirm-dialog';
import { Tag } from '../../../core/api/tags-api';
import { TagsStore } from '../tags.store';

// Tags aren't scoped to the signed-in user by the API (any tag on any
// resource_id comes back from GET /tags) — this is a browse-everything
// page, not "my tags". A todo's own tags are managed from its edit form
// instead (todo-form.ts), via that todo's `tags`/`addTag` links.
@Component({
  selector: 'app-tags-page',
  providers: [TagsStore],
  imports: [
    DatePipe,
    MatButtonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatTableModule,
  ],
  templateUrl: './tags-page.html',
  styleUrl: './tags-page.scss',
})
export class TagsPage {
  protected readonly store = inject(TagsStore);
  private readonly dialog = inject(MatDialog);

  protected readonly displayedColumns = ['tag', 'resource_id', 'created_date', 'actions'];

  protected setSearch(value: string): void {
    this.store.search.set(value);
  }

  protected canDelete(tag: Tag): boolean {
    return tag.links['delete'] !== undefined;
  }

  protected async deleteTag(tag: Tag): Promise<void> {
    const confirmed = await firstValueFrom(
      this.dialog
        .open(ConfirmDialog, {
          data: {
            title: 'Delete tag',
            message: `Delete "${tag.tag}"? This can't be undone.`,
            confirmLabel: 'Delete',
            tone: 'danger',
          },
        })
        .afterClosed(),
    );

    if (confirmed) {
      await this.store.deleteTag(tag);
    }
  }
}
