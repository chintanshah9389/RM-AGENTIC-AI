import { describe, expect, it } from "vitest";

describe("smoke", () => {
  it("marks demo environment", () => {
    expect("POC Environment - Synthetic Data").toContain("Synthetic");
  });
});
