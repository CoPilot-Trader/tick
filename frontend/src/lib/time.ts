/**
 * Eastern-time formatting helpers.
 *
 * The platform standardizes ALL user-facing times to US Eastern (America/New_York)
 * because that's the market timezone traders think in. America/New_York handles
 * EST/EDT daylight-saving transitions automatically.
 */

const ET = 'America/New_York';

/** "9:45:30 AM" style time, Eastern. */
export function formatEasternTime(input: Date | string | number, withSeconds = true): string {
  const d = toDate(input);
  if (!d) return '';
  return d.toLocaleTimeString('en-US', {
    timeZone: ET,
    hour: '2-digit',
    minute: '2-digit',
    ...(withSeconds ? { second: '2-digit' } : {}),
    hour12: true,
  });
}

/** "May 18, 2026" style date, Eastern. */
export function formatEasternDate(input: Date | string | number): string {
  const d = toDate(input);
  if (!d) return '';
  return d.toLocaleDateString('en-US', {
    timeZone: ET,
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

/** "May 18, 9:45 AM ET" compact datetime, Eastern. */
export function formatEasternDateTime(input: Date | string | number): string {
  const d = toDate(input);
  if (!d) return '';
  const date = d.toLocaleDateString('en-US', { timeZone: ET, month: 'short', day: 'numeric' });
  const time = d.toLocaleTimeString('en-US', { timeZone: ET, hour: '2-digit', minute: '2-digit', hour12: true });
  return `${date}, ${time} ET`;
}

/**
 * Format a lightweight-charts time value (UNIX seconds or business-day object)
 * as an Eastern-time axis label. Used for tickMarkFormatter / crosshair.
 */
export function formatEasternAxis(timeValue: number, withTime: boolean): string {
  // lightweight-charts passes UNIX seconds for intraday, or {year,month,day} for daily+
  const d = new Date(timeValue * 1000);
  if (isNaN(d.getTime())) return '';
  if (withTime) {
    return d.toLocaleTimeString('en-US', { timeZone: ET, hour: '2-digit', minute: '2-digit', hour12: false });
  }
  return d.toLocaleDateString('en-US', { timeZone: ET, month: 'short', day: 'numeric' });
}

function toDate(input: Date | string | number): Date | null {
  if (input instanceof Date) return isNaN(input.getTime()) ? null : input;
  const d = new Date(input);
  return isNaN(d.getTime()) ? null : d;
}
