const [operation, path, text = ""] = Deno.args;
switch (operation) {
  case "new":
    await Deno.writeTextFile(path, text, { createNew: true });
    break;
  case "replace":
    await Deno.writeTextFile(path, text);
    break;
  case "read":
    console.log(JSON.stringify(await Deno.readTextFile(path)));
    break;
  case "missing":
    try {
      await Deno.readTextFile(path);
      console.log(JSON.stringify({ missing: false }));
    } catch (error) {
      if (!(error instanceof Deno.errors.NotFound)) throw error;
      console.log(JSON.stringify({ missing: true }));
    }
    break;
  case "list": {
    const files = [];
    for await (const entry of Deno.readDir(path)) {
      if (entry.isFile) files.push(entry.name);
    }
    console.log(JSON.stringify(files.sort()));
    break;
  }
  case "child": {
    const output = await new Deno.Command(Deno.execPath(), {
      args: ["run", new URL("./child.ts", import.meta.url).href],
      stdout: "piped",
      stderr: "piped",
    }).output();
    console.log(JSON.stringify({
      code: output.code,
      stdout: new TextDecoder().decode(output.stdout),
      stderr: new TextDecoder().decode(output.stderr),
    }));
    break;
  }
  default:
    throw new Error("unknown operation");
}
