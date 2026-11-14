import { expect, it } from "vitest";
import { formatMXN } from "./format";

it("formatea pesos sin decimales", () => {
  expect(formatMXN(12500)).toBe("$12,500");
  expect(formatMXN(4_850_000)).toBe("$4,850,000");
});
