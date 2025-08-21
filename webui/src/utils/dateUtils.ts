/**
 * Date utility functions for month calculations
 */

/**
 * Get the current year and month in YYYY-MM format
 */
export function getCurrentYearMonth(date?: Date): string {
  const now = date || new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  return `${year}-${month}`;
}

/**
 * Get all months from January of current year to current month
 */
export function getYearToDateMonths(date?: Date): string[] {
  const now = date || new Date();
  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth() + 1;

  const months: string[] = [];
  for (let month = 1; month <= currentMonth; month++) {
    const monthStr = String(month).padStart(2, '0');
    months.push(`${currentYear}-${monthStr}`);
  }

  return months;
}

/**
 * Get the last 12 months from current month backwards
 */
export function getLast12Months(date?: Date): string[] {
  const now = date || new Date();
  const months: string[] = [];

  // Start from 11 months ago and go to current month
  for (let i = 11; i >= 0; i--) {
    const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    months.push(`${year}-${month}`);
  }

  return months;
}

/**
 * Validate if a string is in valid YYYY-MM format
 */
export function isValidMonthFormat(monthStr: string): boolean {
  const regex = /^\d{4}-\d{2}$/;
  if (!regex.test(monthStr)) return false;

  const [yearStr, monthStr2] = monthStr.split('-');
  const year = parseInt(yearStr, 10);
  const month = parseInt(monthStr2, 10);

  return year >= 1900 && year <= 2100 && month >= 1 && month <= 12;
}

/**
 * Sort months in chronological order (earliest to latest)
 */
export function sortMonthsChronologically(months: string[]): string[] {
  return [...months].sort((a, b) => {
    const [yearA, monthA] = a.split('-').map(Number);
    const [yearB, monthB] = b.split('-').map(Number);

    if (yearA !== yearB) return yearA - yearB;
    return monthA - monthB;
  });
}

/**
 * Sort months in reverse chronological order (latest to earliest)
 */
export function sortMonthsReverseChronologically(months: string[]): string[] {
  return [...months].sort((a, b) => {
    const [yearA, monthA] = a.split('-').map(Number);
    const [yearB, monthB] = b.split('-').map(Number);

    if (yearA !== yearB) return yearB - yearA;
    return monthB - monthA;
  });
}
