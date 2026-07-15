import type { GroupedDataItem, MismatchItem } from '../services/api';

export const SOAP_MASHUP_EXCLUSION_TOOLTIP =
  'Excluded from distinct soap/scent metrics (soaps table, unique_soaps, diversity). ' +
  'Still counted in mashup usage; affects Boring Score via total shaves.';

export const SOAP_MASHUP_BADGE_SOURCES_TOOLTIP =
  'Mashup badge when: enrich marked is_mashup (enable Use enriched data after running enrich), ' +
  'or matched.countable is false from catalog.';

export const SOAP_MASHUP_MATCH_ONLY_NOTE =
  'Showing matched data only. Mashup badges use catalog non-countable scents (countable: false). ' +
  'Text-detected mashups appear after you run enrich and enable Use enriched data.';

type SoapMashupCheckInput = {
  matched?: Record<string, unknown> | null;
  enriched?: Record<string, unknown> | null;
};

/** Mashup exclusion uses enrich-phase is_mashup or catalog countable:false only. */
export function isSoapMashupExcluded(field: string, item: SoapMashupCheckInput): boolean {
  if (field !== 'soap') {
    return false;
  }

  if (item.enriched?.is_mashup === true) {
    return true;
  }

  const matched = item.matched;
  if (matched && typeof matched === 'object' && matched.countable === false) {
    return true;
  }

  return false;
}

export function isGroupedSoapMashupExcluded(field: string, item: GroupedDataItem): boolean {
  if (field !== 'soap') {
    return false;
  }

  if (item.is_mashup === true) {
    return true;
  }

  return item.countable === false;
}

export function mismatchItemShowsMashupExclusion(field: string, item: MismatchItem): boolean {
  return isSoapMashupExcluded(field, item);
}
