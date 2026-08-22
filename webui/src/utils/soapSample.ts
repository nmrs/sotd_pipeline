import type { GroupedDataItem, MismatchItem } from '../services/api';

export const SOAP_SAMPLE_USAGE_TOOLTIP =
  'Detected as sample usage from enrich (sample_type). ' +
  'Enable Use enriched data after running enrich to see this badge.';

export const SOAP_SAMPLE_BADGE_SOURCES_TOOLTIP =
  'Sample badge when soap.enriched.sample_type is set (e.g. sample, tester).';

type SoapSampleCheckInput = {
  enriched?: Record<string, unknown> | null;
  sample_type?: string | null;
};

function normalizeSampleType(value: unknown): string | null {
  if (typeof value !== 'string') {
    return null;
  }
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

/** Return sample_type string when present on enriched or grouped item. */
export function getSoapSampleType(item: SoapSampleCheckInput): string | null {
  if (item.sample_type != null) {
    return normalizeSampleType(item.sample_type);
  }
  return normalizeSampleType(item.enriched?.sample_type);
}

/** Sample usage badge when enrich set a non-empty sample_type. */
export function isSoapSampleUsage(field: string, item: SoapSampleCheckInput): boolean {
  if (field !== 'soap') {
    return false;
  }
  return getSoapSampleType(item) !== null;
}

export function isGroupedSoapSampleUsage(field: string, item: GroupedDataItem): boolean {
  if (field !== 'soap') {
    return false;
  }
  return normalizeSampleType(item.sample_type) !== null;
}

export function mismatchItemShowsSampleUsage(field: string, item: MismatchItem): boolean {
  return isSoapSampleUsage(field, item);
}
