import type { ILink } from '@wiliamferraciolli/ngx-api-client';

// Domain shape only — the fetch/create/delete mechanics live in
// ApiClientService (tags.store.ts, todo-form.ts), not here.
export interface Tag {
  id: string;
  resource_id: string;
  tag: string;
  created_date: string;
  links: Record<string, ILink>;
}
