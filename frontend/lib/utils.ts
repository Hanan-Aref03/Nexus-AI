/** Small shared utility helpers for the dashboard layer. */

export function cn(...values: Array<string | false | null | undefined>): string {
  return values.filter(Boolean).join(" ");
}
