// Mirrors the FastAPI/D1 API's response envelope (see fastapi-cloudflare-d1's
// src/api_response.py, src/models.py). Every endpoint returns this shape:
// `_data` keyed by the resource's singular name (a single item or a list of
// them), `_metadata` describing per-field validation/selector options, and
// `_metaLinks` for collection-level actions (e.g. createTodo). Each item in
// `_data` also carries its own `links` map (models.py's `LinkedResource`) —
// self/update/delete/etc, calculated per request by the backend service.
//
// The UI never reconstructs a resource URL itself: every mutation follows
// a href out of one of these link maps instead (see todos.store.ts,
// tags.store.ts, current-user.store.ts's `myTodos`).

export interface Link {
  href: string;
  method: string;
}

// Arbitrary link names (self/update/delete/addTag/tags/myTodos/…) — the set
// depends on the resource and the backend's business rules for the current
// request, so this stays a bag of Links rather than a handful of fixed keys.
export type Links = Record<string, Link>;

export interface MetadataValue {
  id: string;
  value: string;
}

export interface FieldMetadata {
  mandatory?: boolean;
  readOnly?: boolean;
  hidden?: boolean;
  values?: MetadataValue[];
}

export interface Envelope<T> {
  _data: Record<string, T>;
  _metadata?: Record<string, FieldMetadata>;
  _metaLinks?: Links;
}

export function unwrapData<T>(envelope: Envelope<T>, resourceKey: string): T | undefined {
  return envelope._data[resourceKey];
}

export function fieldOptions(envelope: Envelope<unknown>, field: string): MetadataValue[] {
  return envelope._metadata?.[field]?.values ?? [];
}

// A collection-level link (e.g. `_metaLinks.createTodo`) — read the href
// from the API's own response rather than hardcoding the collection URL.
export function metaLink(envelope: Envelope<unknown> | undefined, name: string): string | undefined {
  return envelope?._metaLinks?.[name]?.href;
}
