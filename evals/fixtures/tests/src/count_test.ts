import { assertEquals, assertThrows } from "@std/assert";
import { parseCount } from "./count.ts";

Deno.test("valid count", () => assertEquals(parseCount("2"), 2));
Deno.test("invalid count", () => {
  assertThrows(() => parseCount("-1"), RangeError);
});
Deno.test("async completion", async () => {
  await Promise.resolve();
  assertEquals(parseCount("3"), 3);
  assertEquals({ values: [1, 2], name: "Ada" }, { name: "Ada", values: [1, 2] });
});
Deno.test("nested assertions", async (context) => {
  await context.step("one", () => assertEquals(parseCount("1"), 1));
  await context.step("four", () => assertEquals(parseCount("4"), 4));
});
Deno.test({
  name: "expensive opt-in",
  ignore: true,
  fn: () => { throw new Error("must remain skipped"); },
});
