/**
 * Unit tests for productDataFormatter utility functions.
 */

import { formatMatchedData } from '../productDataFormatter';

describe('formatMatchedData', () => {
  describe('razor field with enriched format', () => {
    it('should use enriched format when available', () => {
      const matched = {
        brand: 'Other Shavette',
        model: '',
        format: 'Shavette',
      };
      const enriched = {
        format: 'Shavette (AC)',
      };

      const result = formatMatchedData(matched, 'razor', enriched);
      expect(result).toBe('Other Shavette - Shavette (AC)');
    });

    it('should use enriched format even when matched format exists', () => {
      const matched = {
        brand: 'Gillette',
        model: 'Tech',
        format: 'DE',
      };
      const enriched = {
        format: 'DE',
      };

      const result = formatMatchedData(matched, 'razor', enriched);
      expect(result).toBe('Gillette - Tech - DE');
    });

    it('should fall back to matched format when enriched format not available', () => {
      const matched = {
        brand: 'Other Shavette',
        model: '',
        format: 'Shavette',
      };
      const enriched = {};

      const result = formatMatchedData(matched, 'razor', enriched);
      expect(result).toBe('Other Shavette - Shavette');
    });

    it('should fall back to matched format when enriched is null', () => {
      const matched = {
        brand: 'Other Shavette',
        model: '',
        format: 'Shavette',
      };

      const result = formatMatchedData(matched, 'razor', null);
      expect(result).toBe('Other Shavette - Shavette');
    });

    it('should fall back to matched format when enriched is undefined', () => {
      const matched = {
        brand: 'Other Shavette',
        model: '',
        format: 'Shavette',
      };

      const result = formatMatchedData(matched, 'razor');
      expect(result).toBe('Other Shavette - Shavette');
    });

    it('should handle enriched format with empty string', () => {
      const matched = {
        brand: 'Other Shavette',
        model: '',
        format: 'Shavette',
      };
      const enriched = {
        format: '',
      };

      const result = formatMatchedData(matched, 'razor', enriched);
      // Should fall back to matched format when enriched format is empty
      expect(result).toBe('Other Shavette - Shavette');
    });

    it('should handle Shavette with DE blade conversion', () => {
      const matched = {
        brand: 'Other Shavette',
        model: '',
        format: 'Shavette',
      };
      const enriched = {
        format: 'Shavette (Half DE)',
      };

      const result = formatMatchedData(matched, 'razor', enriched);
      expect(result).toBe('Other Shavette - Shavette (Half DE)');
    });

    it('should handle Shavette with AC blade', () => {
      const matched = {
        brand: 'Other Shavette',
        model: '',
        format: 'Shavette',
      };
      const enriched = {
        format: 'Shavette (AC)',
      };

      const result = formatMatchedData(matched, 'razor', enriched);
      expect(result).toBe('Other Shavette - Shavette (AC)');
    });

    it('should include brand and model with enriched format', () => {
      const matched = {
        brand: 'Gillette',
        model: 'Super Speed',
        format: 'DE',
      };
      const enriched = {
        format: 'DE',
      };

      const result = formatMatchedData(matched, 'razor', enriched);
      expect(result).toBe('Gillette - Super Speed - DE');
    });
  });

  describe('razor field without enriched format', () => {
    it('should use matched format when no enriched data', () => {
      const matched = {
        brand: 'Gillette',
        model: 'Tech',
        format: 'DE',
      };

      const result = formatMatchedData(matched, 'razor');
      expect(result).toBe('Gillette - Tech - DE');
    });

    it('should handle razor with no format', () => {
      const matched = {
        brand: 'Gillette',
        model: 'Tech',
      };

      const result = formatMatchedData(matched, 'razor');
      expect(result).toBe('Gillette - Tech');
    });
  });

  describe('other fields should be unaffected', () => {
    it('should not use enriched format for blade field', () => {
      const matched = {
        brand: 'Feather',
        model: 'Hi-Stainless',
        format: 'DE',
      };
      const enriched = {
        format: 'AC', // This should be ignored for blade
      };

      const result = formatMatchedData(matched, 'blade', enriched);
      expect(result).toBe('Feather - Hi-Stainless - DE');
    });

    it('should not use enriched format for brush field', () => {
      const matched = {
        brand: 'AP Shave Co',
        model: 'G5C',
      };
      const enriched = {
        format: 'Some Format', // This should be ignored for brush
      };

      const result = formatMatchedData(matched, 'brush', enriched);
      // Brush formatting logic is more complex, just verify it doesn't use enriched.format
      expect(result).not.toContain('Some Format');
    });

    it('should not use enriched format for soap field', () => {
      const matched = {
        brand: 'Declaration Grooming',
        scent: 'Persephone',
      };
      const enriched = {
        format: 'Some Format', // This should be ignored for soap
      };

      const result = formatMatchedData(matched, 'soap', enriched);
      expect(result).toBe('Declaration Grooming - Persephone');
      expect(result).not.toContain('Some Format');
    });
  });

  describe('edge cases', () => {
    it('should handle null matched data', () => {
      const result = formatMatchedData(null, 'razor');
      expect(result).toBe('N/A');
    });

    it('should handle undefined matched data', () => {
      const result = formatMatchedData(undefined, 'razor');
      expect(result).toBe('N/A');
    });

    it('should handle string matched data', () => {
      const result = formatMatchedData('Some String', 'razor');
      expect(result).toBe('Some String');
    });

    it('should handle enriched as string (should be ignored)', () => {
      const matched = {
        brand: 'Other Shavette',
        format: 'Shavette',
      };
      const enriched = 'not an object';

      const result = formatMatchedData(matched, 'razor', enriched);
      // Should fall back to matched format since enriched is not an object
      expect(result).toBe('Other Shavette - Shavette');
    });
  });
});

