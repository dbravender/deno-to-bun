import { name } from "@lib/name.ts";

const node = <span>Hello {name}</span>;
const element = document.getElementById("app");
if (!element) throw new Error("missing app element");
element.textContent = [node.props.children].flat().join("");
