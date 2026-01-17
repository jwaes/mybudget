/**
 * Month navigator component.
 *
 * Allows navigation between budget months.
 */

interface MonthNavigatorProps {
  /** Current month in YYYY-MM format */
  month: string
  /** Callback when month changes */
  onMonthChange: (month: string) => void
}

/**
 * Parse month string to year and month number.
 */
function parseMonth(monthStr: string): { year: number; month: number } {
  const parts = monthStr.split('-')
  const yearPart = parts[0] ?? '2026'
  const monthPart = parts[1] ?? '01'
  return { year: parseInt(yearPart, 10), month: parseInt(monthPart, 10) }
}

/**
 * Format year and month to YYYY-MM string.
 */
function formatMonth(year: number, month: number): string {
  return `${year}-${String(month).padStart(2, '0')}`
}

/**
 * Get display name for a month (e.g., "January 2026").
 */
function getMonthDisplayName(monthStr: string): string {
  const { year, month } = parseMonth(monthStr)
  const date = new Date(year, month - 1, 1)
  return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
}

/**
 * Get the previous month.
 */
function getPreviousMonth(monthStr: string): string {
  const { year, month } = parseMonth(monthStr)
  if (month === 1) {
    return formatMonth(year - 1, 12)
  }
  return formatMonth(year, month - 1)
}

/**
 * Get the next month.
 */
function getNextMonth(monthStr: string): string {
  const { year, month } = parseMonth(monthStr)
  if (month === 12) {
    return formatMonth(year + 1, 1)
  }
  return formatMonth(year, month + 1)
}

export function MonthNavigator({ month, onMonthChange }: MonthNavigatorProps) {
  return (
    <div className="month-navigator">
      <button
        className="nav-button"
        onClick={() => onMonthChange(getPreviousMonth(month))}
        aria-label="Previous month"
      >
        ‹
      </button>
      <span className="month-display">{getMonthDisplayName(month)}</span>
      <button
        className="nav-button"
        onClick={() => onMonthChange(getNextMonth(month))}
        aria-label="Next month"
      >
        ›
      </button>

      <style>{`
        .month-navigator {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .nav-button {
          background: none;
          border: 1px solid #ccc;
          border-radius: 4px;
          padding: 0.5rem 1rem;
          font-size: 1.25rem;
          cursor: pointer;
          color: #333;
        }

        .nav-button:hover {
          background-color: #f0f0f0;
        }

        .month-display {
          font-size: 1.25rem;
          font-weight: 600;
          min-width: 180px;
          text-align: center;
        }
      `}</style>
    </div>
  )
}

export default MonthNavigator
