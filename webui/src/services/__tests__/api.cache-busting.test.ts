// Import the actual API functions to check their implementation
import { analyzeUnmatched, checkFilteredStatus } from '../api';

describe('API Cache-Busting Tests', () => {
  describe('Manual Cache-Busting Detection', () => {
    test('should not contain manual _t= parameters in API function implementations', () => {
      // Get the function source code by converting to string
      const analyzeUnmatchedSource = analyzeUnmatched.toString();
      const checkFilteredStatusSource = checkFilteredStatus.toString();

      // Check for manual _t= parameters in the function implementations
      const manualCacheBustingPatterns = [
        /\?_t=\$\{Date\.now\(\)\}/g,
        /&_t=\$\{Date\.now\(\)\}/g,
        /_t=\$\{Date\.now\(\)\}/g,
      ];

      let foundManualCacheBusting = false;
      const foundPatterns: string[] = [];

      // Check both functions
      [analyzeUnmatchedSource, checkFilteredStatusSource].forEach((source, funcIndex) => {
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
        console.error('Function sources containing manual cache-busting:');
        console.error('analyzeUnmatched:', analyzeUnmatchedSource);
        console.error('checkFilteredStatus:', checkFilteredStatusSource);
      }

      expect(foundManualCacheBusting).toBe(false);
    });
  });

  describe('Axios Interceptor Validation', () => {
    test('should have cache-busting interceptor configured in API source', () => {
      // Check that the API source contains the interceptor configuration
      const analyzeUnmatchedSource = analyzeUnmatched.toString();
      const checkFilteredStatusSource = checkFilteredStatus.toString();

      // The functions should not contain manual cache-busting
      expect(analyzeUnmatchedSource).not.toContain('_t=${Date.now()}');
      expect(checkFilteredStatusSource).not.toContain('_t=${Date.now()}');

      // The functions should use simple URLs without manual cache-busting
      expect(analyzeUnmatchedSource).toContain('/analysis/unmatched');
      expect(checkFilteredStatusSource).toContain('/filtered/check');
    });
  });
});
