// Mirrors the API's response envelope (see resource-management-api's
// docs/backend-conventions.md). Every endpoint returns this shape:
// `_data` keyed by the resource's singular name (a single item or a list
// of them), `_metadata` describing field validation/selector options,
// `_metaLinks` pointing at the collection endpoint.

export interface Link {
  href: string;
}

export interface ResourceLinks {
  self?: Link;
  update?: Link;
  delete?: Link;
}

export interface MetadataValue {
  id: string;
  value: string;
}

export interface FieldMetadata {
  mandatory: boolean;
  values?: MetadataValue[];
}

export interface Envelope<T> {
  _data: Record<string, T>;
  _metadata?: Record<string, FieldMetadata>;
  _metaLinks?: Record<string, Link>;
}

export function unwrapData<T>(envelope: Envelope<T>, resourceKey: string): T | undefined {
  return envelope._data[resourceKey];
}

export function fieldOptions(envelope: Envelope<unknown>, field: string): MetadataValue[] {
  return envelope._metadata?.[field]?.values ?? [];
}
