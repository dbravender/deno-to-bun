import { opendir, readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const [operation, path, text = ""] = process.argv.slice(2);
switch (operation) {
  case "new":
    await writeFile(path, text, { encoding: "utf8", flag: "wx" });
    break;
  case "replace":
    await writeFile(path, text, "utf8");
    break;
  case "read":
    console.log(JSON.stringify(await readFile(path, "utf8")));
    break;
  case "missing":
    try {
      await readFile(path, "utf8");
      console.log(JSON.stringify({ missing: false }));
    } catch (error) {
      if (!(error instanceof Error && "code" in error && error.code === "ENOENT")) throw error;
      console.log(JSON.stringify({ missing: true }));
    }
    break;
  case "list": {
    const files = [];
    for await (const entry of await opendir(path)) {
      if (entry.isFile()) files.push(entry.name);
    }
    console.log(JSON.stringify(files.sort()));
    break;
  }
  case "child": {
    const child = Bun.spawn([
      process.execPath,
      fileURLToPath(new URL("./child.ts", import.meta.url)),
    ], { stdout: "pipe", stderr: "pipe" });
    const [stdout, stderr, code] = await Promise.all([
      new Response(child.stdout).text(),
      new Response(child.stderr).text(),
      child.exited,
    ]);
    console.log(JSON.stringify({ code, stdout, stderr }));
    break;
  }
  default:
    throw new Error("unknown operation");
}
