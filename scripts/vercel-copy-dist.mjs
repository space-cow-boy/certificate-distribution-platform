import { cpSync, existsSync, rmSync } from "node:fs";
import { resolve } from "node:path";

const from = resolve("frontend", "dist");
const to = resolve("dist");

if (!existsSync(from)) {
  console.error(`Expected build output at ${from} but it does not exist.`);
  process.exit(1);
}

if (existsSync(to)) {
  rmSync(to, { recursive: true, force: true });
}

cpSync(from, to, { recursive: true });
console.log(`Copied ${from} -> ${to}`);
