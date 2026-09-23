import { Component, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormField, FormRoot, form, required, schema } from '@angular/forms/signals';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { LinkService } from '@wiliamferraciolli/ngx-api-client';
import { firstValueFrom } from 'rxjs';

import { ConfirmDialog } from '../../../shared/confirm-dialog/confirm-dialog';
import { describeApiError } from '../../../core/api/api-error';
import { Tag } from '../../../core/api/tags-api';
import { TagsStore } from '../tags.store';

interface NewTagFormModel {
  tag: string;
  resource_id: string;
}

const INITIAL_NEW_TAG: NewTagFormModel = { tag: '', resource_id: '' };

const newTagSchema = schema<NewTagFormModel>((path) => {
  required(path.tag);
  required(path.resource_id);
});

// A small, muted, fixed palette — not decoration, but a categorical key:
// the same tag text always lands on the same swatch, so a repeated tag
// (e.g. "urgent") is recognisable by color alone once you've seen it once.
// Deliberately soft (low-saturation) rather than the loud primaries a chip
// picker would default to.
const TAG_PALETTE = ['#6366A8', '#3E7D5D', '#B4732C', '#B34A66', '#2C7B8C', '#7A4FA3'];

function tagColor(tag: string): string {
  let hash = 0;
  for (let i = 0; i < tag.length; i++) {
    hash = (hash * 31 + tag.charCodeAt(i)) | 0;
  }
  return TAG_PALETTE[Math.abs(hash) % TAG_PALETTE.length];
}

// Tags aren't scoped to the signed-in user by the API (any tag on any
// resource_id comes back from GET /tags) — this is a browse-everything page,
// not "my tags". A todo's own tags can still be managed from its edit form
// (todo-form.ts), via that todo's `tags`/`addTag` links; this page is the
// general-purpose workbench for tagging any resource by id and cleaning up
// after it.
@Component({
  selector: 'app-tags-page',
  providers: [TagsStore],
  imports: [
    DatePipe,
    FormField,
    FormRoot,
    MatButtonModule,
    MatChipsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
  ],
  templateUrl: './tags-page.html',
  styleUrl: './tags-page.scss',
})
export class TagsPage {
  protected readonly store = inject(TagsStore);
  protected readonly links = inject(LinkService);
  private readonly dialog = inject(MatDialog);

  protected readonly newTagModel = signal<NewTagFormModel>(INITIAL_NEW_TAG);
  protected readonly createError = signal<string | null>(null);
  protected readonly creating = signal(false);

  protected readonly newTagForm = form(this.newTagModel, newTagSchema, {
    submission: {
      action: async () => {
        this.createError.set(null);
        this.creating.set(true);
        try {
          await this.store.createTag(this.newTagModel());
          // Clears both the value and the touched/dirty state — a plain
          // `newTagModel.set(...)` would leave the fields touched, so
          // they'd immediately redisplay "Required" against the fresh
          // empty values.
          this.newTagForm().reset(INITIAL_NEW_TAG);
        } catch (err) {
          this.createError.set(this.extractErrorMessage(err));
        } finally {
          this.creating.set(false);
        }
        return undefined;
      },
    },
  });

  protected setSearch(value: string): void {
    this.store.search.set(value);
  }

  protected tagColor(tag: string): string {
    return tagColor(tag);
  }

  protected canDelete(tag: Tag): boolean {
    return this.links.hasLink(tag.links['delete']);
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

  private extractErrorMessage(err: unknown): string {
    return describeApiError(err, 'Failed to create tag.');
  }
}
