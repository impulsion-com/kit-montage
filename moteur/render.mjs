#!/usr/bin/env node
// Rendu d'un plan : node render.mjs <plan.json> <sortie.mp4> [--crf 17] [--still <ms> <png>]
import { bundle } from "@remotion/bundler";
import { renderMedia, renderStill, selectComposition } from "@remotion/renderer";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const here = path.dirname(fileURLToPath(import.meta.url));
const [planPath, outPath, ...rest] = process.argv.slice(2);
if (!planPath || !outPath) {
  console.error("usage: node render.mjs <plan.json> <sortie.mp4> [--crf 17] [--still <ms>]");
  process.exit(1);
}
const crf = rest.includes("--crf") ? Number(rest[rest.indexOf("--crf") + 1]) : 17;
const stillMs = rest.includes("--still") ? Number(rest[rest.indexOf("--still") + 1]) : null;
const inputProps = JSON.parse(fs.readFileSync(planPath, "utf-8"));

const serveUrl = await bundle({ entryPoint: path.join(here, "src/index.ts"), publicDir: path.join(here, "public") });
const composition = await selectComposition({ serveUrl, id: "Reel", inputProps });
if (stillMs !== null) {
  await renderStill({ composition, serveUrl, inputProps, output: outPath, frame: Math.round((stillMs / 1000) * composition.fps) });
  console.log("still →", outPath);
  process.exit(0);
}
const t0 = Date.now();
await renderMedia({
  composition,
  serveUrl,
  inputProps,
  codec: "h264",
  crf,
  outputLocation: outPath,
  concurrency: 4,
  onProgress: ({ progress }) => process.stdout.write(`\r${Math.round(progress * 100)} %`),
});
console.log(`\n→ ${outPath} (${((Date.now() - t0) / 1000).toFixed(0)} s)`);
