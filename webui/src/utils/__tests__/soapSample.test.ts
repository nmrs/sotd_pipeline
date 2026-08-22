import {
  getSoapSampleType,
  isGroupedSoapSampleUsage,
  isSoapSampleUsage,
  mismatchItemShowsSampleUsage,
} from '../soapSample';
import type { GroupedDataItem, MismatchItem } from '../../services/api';

describe('soapSample utils', () => {
  it('detects sample from enriched sample_type', () => {
    expect(
      isSoapSampleUsage('soap', {
        enriched: { sample_type: 'sample' },
      })
    ).toBe(true);
  });

  it('detects tester sample_type', () => {
    expect(
      isSoapSampleUsage('soap', {
        enriched: { sample_type: 'tester' },
      })
    ).toBe(true);
  });

  it('ignores null/empty sample_type', () => {
    expect(
      isSoapSampleUsage('soap', {
        enriched: { sample_type: null },
      })
    ).toBe(false);
    expect(
      isSoapSampleUsage('soap', {
        enriched: { sample_type: '' },
      })
    ).toBe(false);
    expect(isSoapSampleUsage('soap', { enriched: {} })).toBe(false);
  });

  it('only applies to soap field', () => {
    expect(
      isSoapSampleUsage('razor', {
        enriched: { sample_type: 'sample' },
      })
    ).toBe(false);
  });

  it('returns sample type string for tooltip/label helpers', () => {
    expect(getSoapSampleType({ enriched: { sample_type: 'tester' } })).toBe('tester');
    expect(getSoapSampleType({ enriched: { sample_type: null } })).toBeNull();
  });

  it('detects grouped sample from sample_type flag', () => {
    const item: GroupedDataItem = {
      matched_string: 'Stirling Soap Co. - Sample Mashup',
      brand: 'Stirling Soap Co.',
      scent: 'Sample Mashup',
      sample_type: 'sample',
      total_count: 1,
      top_patterns: [],
      remaining_count: 0,
      all_patterns: [],
      pattern_count: 0,
      match_type: 'regex',
      match_type_breakdown: { exact: 0, regex: 1 },
      is_grouped: true,
    };
    expect(isGroupedSoapSampleUsage('soap', item)).toBe(true);
  });

  it('mismatchItemShowsSampleUsage mirrors soap helper', () => {
    const item: MismatchItem = {
      original: 'Stirling VarenBury (combined Varen and Glastonbury 1oz samples)',
      matched: { brand: 'Stirling Soap Co.', scent: 'Sample Mashup', countable: false },
      enriched: { sample_type: 'sample', is_mashup: true },
      mismatch_type: 'good_matches',
      match_type: 'regex',
      pattern: 'varenbury',
      count: 1,
      comment_ids: ['p2yjpzm'],
      examples: [],
    };
    expect(mismatchItemShowsSampleUsage('soap', item)).toBe(true);
  });
});
