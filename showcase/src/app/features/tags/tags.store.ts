import { HttpClient, httpResource } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';

import { Tag, TagsEnvelope, createTag as apiCreateTag, deleteTag as apiDeleteTag } from '../../core/api/tags-api';
import { metaLink, unwrapData } from '../../core/api/envelope';
import { environment } from '../../../environments/environment';

const EMPTY_LIST_ENVELOPE: TagsEnvelope = { _data: { tags: [] } };

// Feature-local state — a plain injectable, per docs/frontend-conventions.md.
// Provided on TagsPage. Tags aren't user-scoped in the API (unlike
// /users/{id}/todos), so this browses every tag rather than following a
// link off /me.
@Injectable()
export class TagsStore {
  private readonly http = inject(HttpClient);

  readonly search = signal('');

  readonly listResource = httpResource<TagsEnvelope>(
    () => {
      const term = this.search().trim();
      return term
        ? `${environment.apiUrl}/tags/search?tag=${encodeURIComponent(term)}`
        : `${environment.apiUrl}/tags`;
    },
    { defaultValue: EMPTY_LIST_ENVELOPE },
  );

  readonly tags = computed(() => unwrapData(this.listResource.value() ?? EMPTY_LIST_ENVELOPE, 'tags') ?? []);
  readonly isLoading = computed(() => this.listResource.isLoading());
  readonly loadError = computed(() => this.listResource.error());

  async createTag(payload: { resource_id: string; tag: string }): Promise<Tag> {
    // Collection's own createTag link — falls back to the well-known
    // `/tags` only if a search result (no createTag meta link) is the
    // last thing loaded. apiCreateTag prefixes environment.apiUrl itself,
    // so this href stays relative either way.
    const href = metaLink(this.listResource.value(), 'createTag') ?? '/tags';
    const tag = await apiCreateTag(this.http, href, payload);
    this.listResource.reload();
    return tag;
  }

  async deleteTag(tag: Tag): Promise<void> {
    await apiDeleteTag(this.http, tag);
    this.listResource.reload();
  }
}
