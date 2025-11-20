/**
 * Unit tests for enrichPhaseUtils utility functions.
 */

import {
  hasEnrichPhaseChanges,
  getEnrichPhaseChanges,
  formatEnrichPhaseChanges,
} from '../enrichPhaseUtils';

describe('enrichPhaseUtils', () => {
  describe('hasEnrichPhaseChanges for razor field', () => {
    it('should detect format change from Shavette to Shavette (AC)', () => {
      const matched = {
        brand: 'Other Shavette',
        format: 'Shavette',
      };
      const enriched = {
        format: 'Shavette (AC)',
      };

      const result = hasEnrichPhaseChanges(matched, enriched, 'razor');
      expect(result).toBe(true);
    });

    it('should detect format change from Shavette to Shavette (Half DE)', () => {
      const matched = {
        brand: 'Other Shavette',
        format: 'Shavette',
      };
      const enriched = {
        format: 'Shavette (Half DE)',
      };

      const result = hasEnrichPhaseChanges(matched, enriched, 'razor');
      expect(result).toBe(true);
    });

    it('should not detect change when formats are the same', () => {
      const matched = {
        brand: 'Gillette',
        format: 'DE',
      };
      const enriched = {
        format: 'DE',
      };

      const result = hasEnrichPhaseChanges(matched, enriched, 'razor');
      expect(result).toBe(false);
    });

    it('should not detect change when enriched format is missing', () => {
      const matched = {
        brand: 'Gillette',
        format: 'DE',
      };
      const enriched = {};

      const result = hasEnrichPhaseChanges(matched, enriched, 'razor');
      expect(result).toBe(false);
    });

    it('should not detect change when enriched is null', () => {
      const matched = {
        brand: 'Gillette',
        format: 'DE',
      };

      const result = hasEnrichPhaseChanges(matched, null as any, 'razor');
      expect(result).toBe(false);
    });
  });

  describe('getEnrichPhaseChanges for razor field', () => {
    it('should return format change from Shavette to Shavette (AC)', () => {
      const matched = {
        brand: 'Other Shavette',
        format: 'Shavette',
      };
      const enriched = {
        format: 'Shavette (AC)',
      };

      const result = getEnrichPhaseChanges(matched, enriched, 'razor');
      expect(result).toHaveLength(1);
      expect(result[0]).toEqual({
        field: 'format',
        originalValue: 'Shavette',
        enrichedValue: 'Shavette (AC)',
        displayName: 'Format',
      });
    });

    it('should return format change from Shavette to Shavette (Half DE)', () => {
      const matched = {
        brand: 'Other Shavette',
        format: 'Shavette',
      };
      const enriched = {
        format: 'Shavette (Half DE)',
      };

      const result = getEnrichPhaseChanges(matched, enriched, 'razor');
      expect(result).toHaveLength(1);
      expect(result[0]).toEqual({
        field: 'format',
        originalValue: 'Shavette',
        enrichedValue: 'Shavette (Half DE)',
        displayName: 'Format',
      });
    });

    it('should return empty array when formats are the same', () => {
      const matched = {
        brand: 'Gillette',
        format: 'DE',
      };
      const enriched = {
        format: 'DE',
      };

      const result = getEnrichPhaseChanges(matched, enriched, 'razor');
      expect(result).toHaveLength(0);
    });

    it('should return empty array when enriched format is missing', () => {
      const matched = {
        brand: 'Gillette',
        format: 'DE',
      };
      const enriched = {};

      const result = getEnrichPhaseChanges(matched, enriched, 'razor');
      expect(result).toHaveLength(0);
    });
  });

  describe('formatEnrichPhaseChanges for razor field', () => {
    it('should format format change correctly', () => {
      const matched = {
        brand: 'Other Shavette',
        format: 'Shavette',
      };
      const enriched = {
        format: 'Shavette (AC)',
      };

      const result = formatEnrichPhaseChanges(matched, enriched, 'razor');
      expect(result).toBe('Format: Shavette → Shavette (AC)');
    });

    it('should return "No changes detected" when formats are the same', () => {
      const matched = {
        brand: 'Gillette',
        format: 'DE',
      };
      const enriched = {
        format: 'DE',
      };

      const result = formatEnrichPhaseChanges(matched, enriched, 'razor');
      expect(result).toBe('No changes detected');
    });
  });
});

