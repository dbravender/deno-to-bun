import { test } from "bun:test";
import { assertEquals, assertThrows } from "@std/assert";
import { parseCount } from "./count.ts";

test("valid count", () => assertEquals(parseCount("2"), 2));
test("invalid count", () => {
  assertThrows(() => parseCount("-1"), RangeError);
});
test("async completion", async () => {
  await Promise.resolve();
  assertEquals(parseCount("3"), 3);
  assertEquals({ values: [1, 2], name: "Ada" }, { name: "Ada", values: [1, 2] });
});
test("nested assertions", () => {
  assertEquals(parseCount("1"), 1);
  assertEquals(parseCount("4"), 4);
});
test.skip("expensive opt-in", () => { throw new Error("must remain skipped"); });
