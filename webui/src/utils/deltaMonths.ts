/**
 * Utility functions for calculating delta months for historical comparison.
 * This mirrors the logic from the CLI's calculate_delta_months function.
 */

export interface DeltaMonthCalculation {
  primaryMonths: string[];
  deltaMonths: string[];
  allMonths: string[];
}

/**
 * Calculate delta months for the given months.
 * For each month, adds: month-1, month-1year, month-5years
 */
export function calculateDeltaMonths(months: string[]): DeltaMonthCalculation {
  if (months.length === 0) {
    return { primaryMonths: [], deltaMonths: [], allMonths: [] };
  }

  const allMonths = new Set<string>(months);
  const deltaMonths = new Set<string>();

  // For each primary month, add historical comparison months
  // Note: Check against the original months set, not the growing allMonths set
  const originalMonths = new Set<string>(months);

  for (const monthStr of months) {
    const [year, month] = monthStr.split('-').map(Number);

    // Month - 1 month
    let oneMonthAgo: string;
    if (month === 1) {
      oneMonthAgo = `${year - 1}-12`;
    } else {
      oneMonthAgo = `${year}-${(month - 1).toString().padStart(2, '0')}`;
    }

    if (!originalMonths.has(oneMonthAgo)) {
      deltaMonths.add(oneMonthAgo);
      allMonths.add(oneMonthAgo);
    }

    // Month - 1 year
    const oneYearAgo = `${year - 1}-${month.toString().padStart(2, '0')}`;
    if (!originalMonths.has(oneYearAgo)) {
      deltaMonths.add(oneYearAgo);
      allMonths.add(oneYearAgo);
    }

    // Month - 5 years
    const fiveYearsAgo = `${year - 5}-${month.toString().padStart(2, '0')}`;
    if (!originalMonths.has(fiveYearsAgo)) {
      deltaMonths.add(fiveYearsAgo);
      allMonths.add(fiveYearsAgo);
    }
  }

  return {
    primaryMonths: months,
    deltaMonths: Array.from(deltaMonths).sort(),
    allMonths: Array.from(allMonths).sort(),
  };
}

/**
 * Format delta months for display
 */
export function formatDeltaMonths(calculation: DeltaMonthCalculation): string {
  if (calculation.deltaMonths.length === 0) {
    return `${calculation.primaryMonths.length} months selected`;
  }

  const primaryCount = calculation.primaryMonths.length;
  const deltaCount = calculation.deltaMonths.length;
  const totalCount = calculation.allMonths.length;

  return `${primaryCount} primary + ${deltaCount} delta = ${totalCount} total months`;
}
