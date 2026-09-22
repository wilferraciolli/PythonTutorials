// Shared by both the global Tags page (tags.store.ts) and Todo form's
// inline "tags on this todo" section — both do the exact same three
// operations against a Tag's own links, just against a different
// starting collection href (all tags vs. one todo's `tags` link), so it's
// plain functions rather than a second feature store to duplicate them in.
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

import { Envelope, Links, unwrapData } from './envelope';
import { environment } from '../../../environments/environment';

export interface Tag {
  id: string;
  resource_id: string;
  tag: string;
  created_date: string;
  links: Links;
}

export type TagsEnvelope = Envelope<Tag[]>;
export type TagEnvelope = Envelope<Tag>;

export async function fetchTags(http: HttpClient, href: string): Promise<Tag[]> {
  const response = await firstValueFrom(http.get<TagsEnvelope>(`${environment.apiUrl}${href}`));
  return unwrapData(response, 'tags') ?? [];
}

export async function createTag(
  http: HttpClient,
  href: string,
  payload: { resource_id: string; tag: string },
): Promise<Tag> {
  const response = await firstValueFrom(http.post<TagEnvelope>(`${environment.apiUrl}${href}`, payload));
  return unwrapData(response, 'tag') as Tag;
}

export async function deleteTag(http: HttpClient, tag: Tag): Promise<void> {
  const url = tag.links['delete']?.href;
  if (!url) throw new Error(`Not permitted to delete tag ${tag.id}`);
  await firstValueFrom(http.delete(`${environment.apiUrl}${url}`));
}
