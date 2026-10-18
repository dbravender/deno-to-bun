#!/usr/bin/env bun
import { greet } from "@lib/greet.ts";

const [name = "world", countText = "1"] = process.argv.slice(2);
const count = Number(countText);
if (!Number.isInteger(count) || count < 1) {
  console.error("count must be a positive integer");
  process.exit(2);
}
console.log(JSON.stringify({
  message: greet(name),
  count,
  mode: process.env.APP_MODE ?? null,
  implicit: process.env.EVAL_IMPLICIT_ENV ?? null,
}));
