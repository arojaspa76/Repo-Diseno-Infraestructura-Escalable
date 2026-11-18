import { describe, expect, it } from "vitest";
import { budgetTone, formatUsd, parseNdjson } from "./lib";

describe("parseNdjson", () => {
  it("parsea líneas completas y conserva la incompleta", () => {
    const { events, rest } = parseNdjson('{"type":"token","text":"ho"}\n{"type":"token","te');
    expect(events).toEqual([{ type: "token", text: "ho" }]);
    expect(rest).toBe('{"type":"token","te');
  });
  it("ignora líneas vacías", () => {
    expect(parseNdjson('\n{"type":"token","text":"a"}\n').events).toHaveLength(1);
  });
});

describe("formatUsd", () => {
  it("usa más decimales para montos pequeños", () => {
    expect(formatUsd(0.0003)).toBe("$0.000300");
    expect(formatUsd(1.5)).toBe("$1.5000");
    expect(formatUsd(0)).toBe("$0");
  });
});

describe("budgetTone", () => {
  it("clasifica los umbrales 50/80", () => {
    expect(budgetTone(10)).toBe("ok");
    expect(budgetTone(50)).toBe("warn");
    expect(budgetTone(80)).toBe("danger");
  });
});
