import type { ILink } from '@wiliamferraciolli/ngx-api-client';

// An embedded reference to another resource — id plus its display value —
// so the UI can show a name without a second lookup. Same id/value shape
// the API uses for metadata option lists (e.g. Todo's `state` values).
export interface EmbeddedRef {
  id: string;
  value: string;
}

// Domain shape only — the fetch/create/delete mechanics live in
// ApiClientService (tags.store.ts, todo-form.ts), not here.
export interface Tag {
  id: string;
  resource_id: string;
  // The resource_id's display name, embedded by the API (tag_resource_view)
  // — null when the resource can't be resolved (e.g. it's been deleted).
  resource: EmbeddedRef | null;
  tag: string;
  created_date: string;
  links: Record<string, ILink>;
}
