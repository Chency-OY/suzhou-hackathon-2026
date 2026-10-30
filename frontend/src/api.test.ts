import { describe, expect, it } from "vitest";
import { apiUrl } from "./api";

describe("API path under a deployed subdirectory", () => {
  it("keeps writes and reads inside the trainer application", () => {
    expect(apiUrl("/sessions", "/rep-trainer/")).toBe("/rep-trainer/api/sessions");
    expect(apiUrl("/scenarios", "/rep-trainer/")).toBe("/rep-trainer/api/scenarios");
  });
});
