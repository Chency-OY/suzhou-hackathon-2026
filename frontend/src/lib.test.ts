import { describe, expect, it } from "vitest";
import { buildQuery } from "./api";
import { END_REASON_LABEL, DEPT_LABEL, DIFFICULTY_LABEL, DIFFICULTY_STYLE, SIGNAL_LABEL, SIGNAL_POLARITY, TYPE_LABEL } from "./labels";
import { getRepId } from "./lib/rep";
import { DEPARTMENTS, DIFFICULTIES, END_REASONS, SCENARIO_TYPES, SIGNALS } from "./types";

describe("buildQuery", () => {
  it("忽略空值并编码", () => {
    expect(buildQuery({})).toBe("");
    expect(buildQuery({ dept: undefined, type: "" })).toBe("");
    expect(buildQuery({ dept: "hepatology", difficulty: "hard" })).toBe("?dept=hepatology&difficulty=hard");
  });
});

describe("labels", () => {
  it("每个枚举值都有中文标签", () => {
    for (const d of DEPARTMENTS) expect(DEPT_LABEL[d]).toBeTruthy();
    for (const d of DIFFICULTIES) {
      expect(DIFFICULTY_LABEL[d]).toBeTruthy();
      expect(DIFFICULTY_STYLE[d]).toBeTruthy();
    }
    for (const t of SCENARIO_TYPES) expect(TYPE_LABEL[t]).toBeTruthy();
  });
});

describe("session labels", () => {
  it("每个信号与结束原因都有标签", () => {
    for (const s of SIGNALS) {
      expect(SIGNAL_LABEL[s]).toBeTruthy();
      expect(["good", "bad"]).toContain(SIGNAL_POLARITY[s]);
    }
    for (const r of END_REASONS) expect(END_REASON_LABEL[r]).toBeTruthy();
  });
  it("getRepId 在无 localStorage 的环境也能返回稳定值", () => {
    const a = getRepId();
    expect(a).toMatch(/^rep_/);
    expect(getRepId()).toBe(a);
  });
});
