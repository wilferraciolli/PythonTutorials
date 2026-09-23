import { httpResource } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { ApiClientService, CollectionEnvelope } from '@wiliamferraciolli/ngx-api-client';

import { describeApiError } from '../../core/api/api-error';
import { Tag } from '../../core/api/tags-api';
import { environment } from '../../../environments/environment';

type TagsEnvelope = CollectionEnvelope<'tags', Tag>;

// Feature-local state — a plain injectable, per docs/frontend-conventions.md.
// Provided on TagsPage. Tags aren't user-scoped in the API (unlike
// /users/{id}/todos), so this browses every tag rather than following a
// link off /me — there's no collection link to resolve, just the
// well-known /tags and /tags/search endpoints.
@Injectable()
export class TagsStore {
  private readonly api = inject(ApiClientService);

  readonly search = signal('');

  private readonly listResource = httpResource<TagsEnvelope>(() => {
    const term = this.search().trim();
    return term
      ? `${environment.apiUrl}/tags/search?tag=${encodeURIComponent(term)}`
      : `${environment.apiUrl}/tags`;
  });

  readonly tags = computed(() => this.listResource.value()?._data['tags'] ?? []);
  readonly isLoading = computed(() => this.listResource.isLoading());
  readonly loadError = computed(() => this.listResource.error());
  readonly loadErrorMessage = computed(() => {
    const error = this.loadError();
    return error ? describeApiError(error, "Couldn't load tags.") : null;
  });

  // The collection's own `createTag` link — tags are the one resource that
  // still POSTs straight to a create link rather than going through a
  // template (there's nothing to default: `tag` and `resource_id` are both
  // freeform), so this is the direct-POST shape the todos flow moved away
  // from.
  async createTag(payload: { tag: string; resource_id: string }): Promise<Tag> {
    const link = this.listResource.value()?._metaLinks?.['createTag'];
    const url = this.api.requireLink(link, 'No create-tag link available yet — try again.');
    const created = await this.api.post<'tag', Tag, { tag: string; resource_id: string }>('tag', url, payload);
    this.listResource.reload();
    return created;
  }

  async deleteTag(tag: Tag): Promise<void> {
    const url = this.api.requireLink(tag.links['delete'], `Not permitted to delete tag ${tag.id}`);
    await this.api.delete(url);
    this.listResource.reload();
  }
}
