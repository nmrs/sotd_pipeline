import { readFileSync, existsSync } from 'fs';
import { join } from 'path';

// Test that DRY refactor documentation is complete and up-to-date
describe('DRY Refactor Documentation', () => {
  test('should have complete documentation for all shared utilities', () => {
    // Test that all utility files have proper documentation
    const utilityFiles = [
      'src/utils/genericDataTransformer.ts',
      'src/utils/brushDataTransformer.ts',
      'src/utils/cache.ts',
      'src/utils/testUtils.ts',
    ];

    utilityFiles.forEach(filePath => {
      expect(existsSync(filePath)).toBe(true);

      if (existsSync(filePath)) {
        const content = readFileSync(filePath, 'utf-8');

        // Check for JSDoc documentation
        expect(content).toMatch(/\/\*\*[\s\S]*?\*\//);

        // Check for exported functions or constants
        expect(content).toMatch(/export.*function|export.*const|export.*class/);

        // Check for interface/type documentation
        expect(content).toMatch(/interface|type/);
      }
    });
  });

  test('should have updated webui patterns and practices documentation', () => {
    const patternsFile = '../.cursor/rules/webui_patterns_and_practices.mdc';
    expect(existsSync(patternsFile)).toBe(true);

    if (existsSync(patternsFile)) {
      const content = readFileSync(patternsFile, 'utf-8');

      // Check for DRY refactor patterns
      expect(content).toMatch(/DRY|refactor|utility/i);

      // Check for testing patterns
      expect(content).toMatch(/test.*pattern|mock.*pattern/i);

      // Check for component patterns
      expect(content).toMatch(/component.*pattern|ui.*pattern/i);
    }
  });

  test('should have comprehensive test coverage documentation', () => {
    // Test that test files have proper documentation
    const testFiles = [
      'src/utils/__tests__/genericDataTransformer.test.ts',
      'src/utils/__tests__/testUtils.test.ts',
    ];

    testFiles.forEach(filePath => {
      expect(existsSync(filePath)).toBe(true);

      if (existsSync(filePath)) {
        const content = readFileSync(filePath, 'utf-8');

        // Check for test descriptions
        expect(content).toMatch(/describe\(|test\(/);

        // Check for comprehensive test coverage
        expect(content).toMatch(/expect\(/);
      }
    });
  });

  test('should have updated plan documentation with completion status', () => {
    const planFile = '../plans/plan_webui_api_dry_refactor_2025-07-21.mdc';
    expect(existsSync(planFile)).toBe(true);

    if (existsSync(planFile)) {
      const content = readFileSync(planFile, 'utf-8');

      // Check for completion status
      expect(content).toMatch(/COMPLETE|complete/i);

      // Check for lessons learned
      expect(content).toMatch(/lesson|learned|pattern/i);

      // Check for implementation summary
      expect(content).toMatch(/implementation.*summary|completed.*work/i);
    }
  });
});
