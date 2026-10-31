import type { AcademicRadar } from "./types";

export function radarRefreshDue(item: AcademicRadar, now = Date.now()): boolean {
  if (!item.auto_refresh) return false;
  const last = Math.max(Date.parse(item.searched_at), item.last_auto_checked_at ? Date.parse(item.last_auto_checked_at) : 0);
  return Number.isFinite(last) && now - last >= 24 * 60 * 60 * 1000;
}
