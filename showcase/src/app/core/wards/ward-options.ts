import { httpResource } from '@angular/common/http';
import { computed } from '@angular/core';

import { environment } from '../../../environments/environment';
import { Envelope, unwrapData } from '../api/envelope';

// There is no `wards` table/endpoint yet in this codebase — the set of
// known ward ids is derived from the beds that already exist, same as
// BedBoardStore.wardIds. Shared here since both the doctors list filter
// and the doctor form's ward selector need the same derived list.

interface BedWardOnly {
  ward_id: string;
}

type BedsEnvelope = Envelope<BedWardOnly[]>;

const EMPTY_BEDS_ENVELOPE: BedsEnvelope = { _data: { bed: [] } };

export function injectWardIds() {
  const bedsResource = httpResource<BedsEnvelope>(() => `${environment.apiUrl}/beds`, {
    defaultValue: EMPTY_BEDS_ENVELOPE,
  });
  return computed(() => {
    const beds = unwrapData(bedsResource.value() ?? EMPTY_BEDS_ENVELOPE, 'bed') ?? [];
    return [...new Set(beds.map((bed) => bed.ward_id))].sort();
  });
}
