import { describe, expect, it } from "vitest";
import { guidedStep } from "./guided";
import { SCENARIO_TYPES, type ScenarioDetail } from "./types";

const scenario = (type: ScenarioDetail["type"], program_id = "general"): ScenarioDetail => ({
  id: `scn_${type}`, type, program_id, persona_id: "person_1", rep_goal: "演练沟通",
  context_brief: "合成情境", opening_line: "您有什么资料？", success_criteria: [], source: "curated",
  department: "endocrinology", difficulty: "normal",
  persona_public: { department: "endocrinology", title: "主任医师", hospital_tier: "三甲", style_hint: "谨慎", difficulty: "normal" },
});

describe("guided training choices", () => {
  it("offers three distinct choices with feedback at each stage for every scenario type", () => {
    for (const type of SCENARIO_TYPES) for (const program of ["general", "xinermei"]) {
      const item = scenario(type, program);
      for (const step of [0, 1, 2]) {
        const question = guidedStep(item, step);
        expect(question?.choices).toHaveLength(3);
        expect(new Set(question?.choices.map((option) => option.text)).size).toBe(3);
        expect(question?.choices.map((option) => option.quality).sort()).toEqual(["partial", "risk", "strong"]);
        expect(question?.choices.every((option) => option.feedback.length > 8)).toBe(true);
      }
      expect(guidedStep(item, 3)).toBeNull();
    }
  });

  it("keeps choices stable so replayed turns match the same feedback", () => {
    const item = scenario("safety_concern", "xinermei");
    expect(guidedStep(item, 1)?.choices).toEqual(guidedStep(item, 1)?.choices);
  });

  it("answers the doctor's concrete opening in curated scenarios", () => {
    const cases = [
      ["scn_005", "post_conference", "不能直接画等号"],
      ["scn_011", "competitor_compare", "不能直接排优劣"],
      ["scn_013", "first_visit", "两份说明书分别对应"],
      ["scn_015", "competitor_compare", "按公开原文核对"],
    ] as const;
    for (const [id, type, phrase] of cases) {
      const options = guidedStep({ ...scenario(type), id }, 0)?.choices;
      expect(options?.find((item) => item.quality === "strong")?.text).toContain(phrase);
    }
  });
});
