import type { FieldDiary } from "./types";

export const MAX_DIARY_CHARS = 16000;

export interface DiaryDraft {
  hospital: string;
  doctorName: string;
  rawText: string;
}

const draftKey = (accountId: string) => `rep-trainer-diary-draft:${accountId}`;

export function readDiaryDraft(accountId: string, storage?: Storage): DiaryDraft | null {
  try {
    const raw = (storage ?? window.localStorage).getItem(draftKey(accountId));
    if (!raw) return null;
    const value: unknown = JSON.parse(raw);
    if (!value || typeof value !== "object") return null;
    const draft = value as Record<string, unknown>;
    if (typeof draft.hospital !== "string" || typeof draft.doctorName !== "string" || typeof draft.rawText !== "string") return null;
    return { hospital: draft.hospital, doctorName: draft.doctorName, rawText: draft.rawText };
  } catch { return null; }
}

export function saveDiaryDraft(accountId: string, draft: DiaryDraft, storage?: Storage): void {
  try {
    const availableStorage = storage ?? window.localStorage;
    if (draft.rawText || draft.hospital || draft.doctorName) availableStorage.setItem(draftKey(accountId), JSON.stringify(draft));
    else availableStorage.removeItem(draftKey(accountId));
  } catch { /* Browsers may disable local storage; the current input remains usable. */ }
}

export interface DiaryDay { key: string; label: string; items: FieldDiary[] }

export function groupDiariesByDay(items: FieldDiary[]): DiaryDay[] {
  const days = new Map<string, DiaryDay>();
  for (const item of items) {
    const date = new Date(item.created_at);
    const key = `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`;
    if (!days.has(key)) days.set(key, {
      key,
      label: date.toLocaleDateString("zh-CN", { year: "numeric", month: "long", day: "numeric", weekday: "long" }),
      items: [],
    });
    days.get(key)!.items.push(item);
  }
  return [...days.values()];
}
