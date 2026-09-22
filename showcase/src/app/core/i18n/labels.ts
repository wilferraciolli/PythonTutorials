// The API sends stable ids, never pre-formatted display text — this is
// where they get translated. Swap this for a real i18n library (e.g.
// @angular/localize) later; the lookup shape stays the same.
//
// `status` doesn't need an entry here — its display values come straight
// from the API's `_metadata.status.values` (see BedBoardStore.statusOptions
// and core/api/envelope.ts), since status is a mandatory/enumerated field
// the backend already describes. `ward_id` isn't (no such metadata exists
// for it yet), so it's translated locally until it is.

const WARD_LABELS: Record<string, string> = {
  icu: 'ICU',
  er: 'Emergency Room',
};

export function wardLabel(wardId: string): string {
  return WARD_LABELS[wardId] ?? wardId;
}

// qualification `type` has no backend metadata (it's a fixed, small enum
// with no per-request selector need beyond the doctor form), so it's
// translated locally like ward_id.
const QUALIFICATION_TYPE_LABELS: Record<string, string> = {
  board_certification: 'Board Certification',
  degree: 'Degree',
  fellowship: 'Fellowship',
  certification: 'Certification',
  other: 'Other',
};

export function qualificationTypeLabel(type: string): string {
  return QUALIFICATION_TYPE_LABELS[type] ?? type;
}

export const QUALIFICATION_TYPES = Object.keys(QUALIFICATION_TYPE_LABELS);
