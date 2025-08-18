import {
    getCurrentYearMonth,
    getYearToDateMonths,
    getLast12Months,
    isValidMonthFormat,
    sortMonthsChronologically,
    sortMonthsReverseChronologically,
} from '../dateUtils';

describe('dateUtils', () => {
    // Test date for consistent results
    const testDate = new Date('2025-01-15T12:00:00Z');

    describe('getCurrentYearMonth', () => {
        it('should return current year and month in YYYY-MM format', () => {
            const result = getCurrentYearMonth(testDate);
            expect(result).toBe('2025-01');
        });

        it('should use current date when no date provided', () => {
            const result = getCurrentYearMonth();
            // This will use the actual current date, so we just verify it's in the right format
            expect(result).toMatch(/^\d{4}-\d{2}$/);
        });
    });

    describe('getYearToDateMonths', () => {
        it('should return all months from January to current month', () => {
            const result = getYearToDateMonths(testDate);
            expect(result).toEqual(['2025-01']);
        });

        it('should handle different months', () => {
            const marchDate = new Date('2025-03-15T12:00:00Z');
            const result = getYearToDateMonths(marchDate);
            expect(result).toEqual(['2025-01', '2025-02', '2025-03']);
        });
    });

    describe('getLast12Months', () => {
        it('should return last 12 months from current month backwards', () => {
            const result = getLast12Months(testDate);
            expect(result).toHaveLength(12);
            expect(result[result.length - 1]).toBe('2025-01'); // Current month
            expect(result[0]).toBe('2024-02'); // 12 months ago
        });

        it('should handle year boundary correctly', () => {
            const decemberDate = new Date('2024-12-15T12:00:00Z');
            const result = getLast12Months(decemberDate);
            expect(result).toHaveLength(12);
            expect(result[result.length - 1]).toBe('2024-12'); // Current month
            expect(result[0]).toBe('2024-01'); // 12 months ago
        });
    });

    describe('isValidMonthFormat', () => {
        it('should validate correct month formats', () => {
            expect(isValidMonthFormat('2025-01')).toBe(true);
            expect(isValidMonthFormat('2024-12')).toBe(true);
            expect(isValidMonthFormat('2023-06')).toBe(true);
        });

        it('should reject invalid month formats', () => {
            expect(isValidMonthFormat('2025-13')).toBe(false); // Invalid month
            expect(isValidMonthFormat('2025-00')).toBe(false); // Invalid month
            expect(isValidMonthFormat('2025-1')).toBe(false);  // Missing leading zero
            expect(isValidMonthFormat('2025')).toBe(false);    // Missing month
            expect(isValidMonthFormat('25-01')).toBe(false);  // Short year
            expect(isValidMonthFormat('2025-01-01')).toBe(false); // Extra day
            expect(isValidMonthFormat('invalid')).toBe(false); // Invalid format
        });
    });

    describe('sortMonthsChronologically', () => {
        it('should sort months in chronological order', () => {
            const months = ['2025-03', '2025-01', '2024-12', '2025-02'];
            const result = sortMonthsChronologically(months);
            expect(result).toEqual(['2024-12', '2025-01', '2025-02', '2025-03']);
        });

        it('should handle empty array', () => {
            const result = sortMonthsChronologically([]);
            expect(result).toEqual([]);
        });

        it('should handle single month', () => {
            const result = sortMonthsChronologically(['2025-01']);
            expect(result).toEqual(['2025-01']);
        });
    });

    describe('sortMonthsReverseChronologically', () => {
        it('should sort months in reverse chronological order', () => {
            const months = ['2025-01', '2025-03', '2024-12', '2025-02'];
            const result = sortMonthsReverseChronologically(months);
            expect(result).toEqual(['2025-03', '2025-02', '2025-01', '2024-12']);
        });

        it('should handle empty array', () => {
            const result = sortMonthsReverseChronologically([]);
            expect(result).toEqual([]);
        });

        it('should handle single month', () => {
            const result = sortMonthsReverseChronologically(['2025-01']);
            expect(result).toEqual(['2025-01']);
        });
    });
});
