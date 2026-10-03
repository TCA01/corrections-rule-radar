/** Civil effective dates never undergo timezone conversion. Instants use Seoul. */
const DAY = 86400000;
export function calendarOrdinal(value: string | null | undefined): number | null {
  if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const [y, m, d] = value.split('-').map(Number);
  const timestamp = Date.UTC(y, m - 1, d);
  if (new Date(timestamp).toISOString().slice(0, 10) !== value) return null;
  return timestamp / DAY;
}
export function seoulCalendarDate(instant: Date = new Date()): string {
  const parts = new Intl.DateTimeFormat('en-US', { timeZone: 'Asia/Seoul', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(instant);
  const get = (key: string) => parts.find(p => p.type === key)!.value;
  return `${get('year')}-${get('month')}-${get('day')}`;
}
export function formatDotDate(value: string | null | undefined): string {
  return calendarOrdinal(value) === null ? value || '-' : value!.replace(/-/g, '.');
}
export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '-';
  if (!/(Z|[+-]\d{2}:\d{2})$/.test(value)) return value;
  const instant = new Date(value);
  if (isNaN(instant.getTime())) return value;
  const parts = new Intl.DateTimeFormat('en-US', { timeZone: 'Asia/Seoul', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(instant);
  const get = (key: string) => parts.find(p => p.type === key)!.value;
  return `${get('year')}.${get('month')}.${get('day')} ${get('hour')}:${get('minute')}`;
}
export function calculateDDay(value: string | null | undefined, instant: Date = new Date()): { dDay: number | null; label: string } {
  const target = calendarOrdinal(value);
  if (target === null) return { dDay: null, label: '-' };
  const diff = target - calendarOrdinal(seoulCalendarDate(instant))!;
  return { dDay: diff, label: diff === 0 ? 'D-DAY' : diff > 0 ? `D-${diff}` : `D+${Math.abs(diff)}` };
}
export function isSameDay(value: string | null | undefined, instant?: Date): boolean { return calculateDDay(value, instant).dDay === 0; }
export function isFutureDate(value: string | null | undefined, instant?: Date): boolean { const d = calculateDDay(value, instant).dDay; return d !== null && d > 0; }
export function isWithinPastDays(value: string | null | undefined, days: number, instant?: Date): boolean { const d = calculateDDay(value, instant).dDay; return d !== null && d <= 0 && d >= -days; }
export function isWithinNextDays(value: string | null | undefined, days: number, instant?: Date): boolean { const d = calculateDDay(value, instant).dDay; return d !== null && d >= 0 && d <= days; }
