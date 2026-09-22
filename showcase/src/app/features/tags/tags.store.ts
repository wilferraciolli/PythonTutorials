import { httpResource } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { ApiClientService, CollectionEnvelope } from '@wiliamferraciolli/ngx-api-client';

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

  async deleteTag(tag: Tag): Promise<void> {
    const url = this.api.requireLink(tag.links['delete'], `Not permitted to delete tag ${tag.id}`);
    await this.api.delete(url);
    this.listResource.reload();
  }
}
