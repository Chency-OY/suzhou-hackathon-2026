import { describe, expect, it } from "vitest";
import { radarRefreshDue } from "./radarLocal";
import type { AcademicRadar } from "./types";

const now = Date.parse("2026-10-31T12:00:00Z");
const item = (extra: Partial<AcademicRadar>): AcademicRadar => ({
  id: "radar_1", owner_id: "synthetic", doctor_name: "甲某", hospital: "某某医院",
  searched_at: "2026-10-29T12:00:00Z", institution_name: "", institution_url: "", search_name: "",
  status: "no_match", works: [], web_sources: [], answer_points: [], web_status: "ok", radar_version: "v2",
  note: "", auto_refresh: false, last_auto_checked_at: null, refresh_error: "", ...extra,
});

describe("radarRefreshDue", () => {
  it("only refreshes explicitly enabled records after 24 hours", () => {
    expect(radarRefreshDue(item({}), now)).toBe(false);
    expect(radarRefreshDue(item({ auto_refresh: true }), now)).toBe(true);
    expect(radarRefreshDue(item({ auto_refresh: true, searched_at: "2026-10-31T11:00:00Z" }), now)).toBe(false);
    expect(radarRefreshDue(item({ auto_refresh: true, last_auto_checked_at: "2026-10-31T10:00:00Z" }), now)).toBe(false);
  });
});
