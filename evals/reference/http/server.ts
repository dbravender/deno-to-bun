import { realpathSync } from "node:fs";
import { readFile } from "node:fs/promises";

const root = realpathSync(process.argv[2]);
const server = Bun.serve({
  hostname: "127.0.0.1",
  port: 0,
  fetch: async (request) => {
    const url = new URL(request.url);
    if (url.pathname === "/health") return Response.json({ ok: true });
    if (url.pathname === "/echo" && request.method === "POST") {
      return new Response(await request.text(), {
        status: 201,
        headers: { "content-type": "text/plain; charset=utf-8" },
      });
    }
    if (url.pathname.startsWith("/static/")) {
      try {
        const file = realpathSync(root + "/" + decodeURIComponent(url.pathname.slice(8)));
        if (!file.startsWith(root + "/")) return new Response("Forbidden", { status: 403 });
        return new Response(await readFile(file));
      } catch {
        return new Response("Not found", { status: 404 });
      }
    }
    return new Response("Not found", { status: 404 });
  },
});
console.log(JSON.stringify({ port: server.port }));
