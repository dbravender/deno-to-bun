#!/usr/bin/env -S deno run --allow-env
import { greet } from "@lib/greet.ts";

const [name = "world", countText = "1"] = Deno.args;
const count = Number(countText);
if (!Number.isInteger(count) || count < 1) {
  console.error("count must be a positive integer");
  Deno.exit(2);
}
console.log(JSON.stringify({
  message: greet(name),
  count,
  mode: Deno.env.get("APP_MODE") ?? null,
  implicit: Deno.env.get("EVAL_IMPLICIT_ENV") ?? null,
}));
