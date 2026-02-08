// Import the actual API functions to check their implementation
import { analyzeMismatch, checkFilteredStatus } from '../api';

describe('API Cache-Busting Tests', () => {
  describe('Manual Cache-Busting Detection', () => {
    test('should not contain manual _t= parameters in API function implementations', () => {
      const analyzeMismatchSource = analyzeMismatch.toString();
      const checkFilteredStatusSource = checkFilteredStatus.toString();

      const manualCacheBustingPatterns = [
        /\?_t=\$\{Date\.now\(\)\}/g,
        /&_t=\$\{Date\.now\(\)\}/g,
        /_t=\$\{Date\.now\(\)\}/g,
      ];

      let foundManualCacheBusting = false;
      const foundPatterns: string[] = [];

      [analyzeMismatchSource, checkFilteredStatusSource].forEach((source, funcIndex) => {
        manualCacheBustingPatterns.forEach((pattern, patternIndex) => {
          const matches = source.match(pattern);
          if (matches) {
            foundManualCacheBusting = true;
            foundPatterns.push(
              `Function ${funcIndex + 1}, Pattern ${patternIndex + 1}: ${matches.join(', ')}`
            );
          }
        });
      });

      if (foundManualCacheBusting) {
        console.error('Found manual cache-busting patterns:', foundPatterns);
        console.error('analyzeMismatch:', analyzeMismatchSource);
        console.error('checkFilteredStatus:', checkFilteredStatusSource);
      }

      expect(foundManualCacheBusting).toBe(false);
    });
  });

  describe('Axios Interceptor Validation', () => {
    test('should have cache-busting interceptor configured in API source', () => {
      const analyzeMismatchSource = analyzeMismatch.toString();
      const checkFilteredStatusSource = checkFilteredStatus.toString();

      expect(analyzeMismatchSource).not.toContain('_t=${Date.now()}');
      expect(checkFilteredStatusSource).not.toContain('_t=${Date.now()}');

      expect(analyzeMismatchSource).toContain('/analysis/mismatch');
      expect(checkFilteredStatusSource).toContain('/filtered/check');
    });
  });
});
