import { describe, expect, it } from "vitest";
import { groupDiariesByDay, readDiaryDraft, saveDiaryDraft } from "./diaryLocal";
import type { FieldDiary } from "./types";

function fakeStorage(): Storage {
  const values = new Map<string, string>();
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => { values.set(key, value); },
    removeItem: (key) => { values.delete(key); },
    clear: () => values.clear(),
    key: (index) => [...values.keys()][index] ?? null,
    get length() { return values.size; },
  };
}

describe("前线日记本", () => {
  it("仅恢复当前账号的本机草稿，清空后移除", () => {
    const storage = fakeStorage();
    const draft = { hospital: "某医院", doctorName: "某主任", rawText: "长口述的开头" };
    saveDiaryDraft("account-a", draft, storage);
    expect(readDiaryDraft("account-a", storage)).toEqual(draft);
    expect(readDiaryDraft("account-b", storage)).toBeNull();
    saveDiaryDraft("account-a", { hospital: "", doctorName: "", rawText: "" }, storage);
    expect(readDiaryDraft("account-a", storage)).toBeNull();
  });

  it("按设备本地日期分组，同一天的多篇原文留在同组", () => {
    const make = (id: string, date: Date) => ({ id, created_at: date.toISOString() }) as FieldDiary;
    const days = groupDiariesByDay([
      make("new-2", new Date(2026, 9, 31, 17)),
      make("new-1", new Date(2026, 9, 31, 9)),
      make("old", new Date(2026, 9, 30, 9)),
    ]);
    expect(days.map((day) => day.items.map((item) => item.id))).toEqual([["new-2", "new-1"], ["old"]]);
    expect(days[0].label).toContain("31");
  });
});
