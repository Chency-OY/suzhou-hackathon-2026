import { describe, expect, it } from "vitest";
import { buildQuery } from "./api";
import { DEPT_LABEL, DIFFICULTY_LABEL, DIFFICULTY_STYLE, TYPE_LABEL } from "./labels";
import { DEPARTMENTS, DIFFICULTIES, SCENARIO_TYPES } from "./types";

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

import { END_REASON_LABEL, SIGNAL_LABEL, SIGNAL_POLARITY } from "./labels";
import { END_REASONS, SIGNALS } from "./types";

describe("session labels", () => {
  it("每个信号与结束原因都有标签", () => {
    for (const s of SIGNALS) {
      expect(SIGNAL_LABEL[s]).toBeTruthy();
      expect(["good", "bad"]).toContain(SIGNAL_POLARITY[s]);
    }
    for (const r of END_REASONS) expect(END_REASON_LABEL[r]).toBeTruthy();
  });
});
