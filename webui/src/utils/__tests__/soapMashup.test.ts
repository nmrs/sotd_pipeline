import {
  isGroupedSoapMashupExcluded,
  isSoapMashupExcluded,
  mismatchItemShowsMashupExclusion,
} from '../soapMashup';
import type { GroupedDataItem, MismatchItem } from '../../services/api';

describe('soapMashup utils', () => {
  it('detects mashup from enriched is_mashup', () => {
    expect(
      isSoapMashupExcluded('soap', {
        matched: { brand: 'Stirling Soap Co.', scent: 'Sample Mash Up' },
        enriched: { is_mashup: true },
      })
    ).toBe(true);
  });

  it('detects mashup from matched countable false', () => {
    expect(
      isSoapMashupExcluded('soap', {
        matched: { brand: "Mama Bear's Soaps", scent: 'Sample Mashup', countable: false },
      })
    ).toBe(true);
  });

  it('does not infer mashup from original text alone', () => {
    expect(
      isSoapMashupExcluded('soap', {
        original: "Lisa's Natural Herbal Creations Mash Up",
        matched: { brand: "Lisa's Naturals", scent: 'Mash Up' },
      })
    ).toBe(false);
  });

  it('does not flag normal soaps', () => {
    expect(
      isSoapMashupExcluded('soap', {
        matched: { brand: 'Barrister and Mann', scent: 'Seville' },
      })
    ).toBe(false);
  });

  it('does not flag non-soap fields', () => {
    expect(
      isSoapMashupExcluded('razor', {
        matched: { brand: 'Test', model: 'Model' },
        enriched: { is_mashup: true },
      })
    ).toBe(false);
  });

  it('detects grouped mashup from is_mashup flag', () => {
    const item: GroupedDataItem = {
      matched_string: 'Stirling Soap Co. - Sample Mash Up',
      brand: 'Stirling Soap Co.',
      scent: 'Sample Mash Up',
      is_mashup: true,
      total_count: 2,
      top_patterns: [],
      remaining_count: 0,
      all_patterns: [],
      pattern_count: 0,
      match_type: 'brand',
      match_type_breakdown: { exact: 0, brand: 2 },
      is_grouped: true,
    };
    expect(isGroupedSoapMashupExcluded('soap', item)).toBe(true);
  });

  it('mismatchItemShowsMashupExclusion mirrors soap helper', () => {
    const item: MismatchItem = {
      original: 'Stirling Sample Mash Up',
      matched: { brand: 'Stirling Soap Co.', scent: 'Sample Mash Up' },
      enriched: { is_mashup: true },
      pattern: 'stirling',
      match_type: 'brand',
      count: 1,
      comment_ids: ['abc'],
      examples: [],
    };
    expect(mismatchItemShowsMashupExclusion('soap', item)).toBe(true);
  });
});
