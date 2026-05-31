#!/usr/bin/env node
// One-shot migration: rename the existing flat skills to the prefixed-namespace
// scheme and normalize their model/context frontmatter (Phase B of the terrain
// re-architecture). Idempotent-ish: skips a mapping whose source dir is gone.
//
// Run from the plugin root:  node scripts/migrate-skills.mjs [--apply]
// Without --apply it prints what it would do (dry run).
import { readdirSync, readFileSync, writeFileSync, existsSync, mkdirSync, cpSync, rmSync, statSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const skills = join(root, "skills");
const apply = process.argv.includes("--apply");

// old folder -> { to, model, context }  (context omitted = inline)
const MAP = {
  // survey & research
  surveyor:            { to: "survey-site",     model: "sonnet", context: "fork" },
  researcher:          { to: "survey-research",  model: "sonnet", context: "fork" },
  // planning & execution
  planner:             { to: "exec-plan",        model: "opus" },
  blueprinter:         { to: "exec-blueprint",   model: "sonnet", context: "fork" },
  worker:              { to: "exec-worker",      model: "haiku",  context: "fork" },
  inspector:           { to: "exec-inspect",     model: "sonnet", context: "fork" },
  philosopher:         { to: "exec-reflect",     model: "sonnet", context: "fork" },
  // design
  "player-house":      { to: "design-house",     model: "opus" },
  "village-planner":   { to: "design-village",   model: "opus" },
  "city-planner":      { to: "design-city",      model: "opus" },
  "building-architect":{ to: "design-building",  model: "opus" },
  "monument-builder":  { to: "design-monument",  model: "opus" },
  "landscape-architect":{ to: "design-grounds",  model: "opus" },
  // systems
  engineer:            { to: "system-redstone",  model: "opus" },
  "transit-architect": { to: "system-transit",   model: "opus" },
  // setup
  "install-mcp-mod":   { to: "setup-mod" },
  "setup-mcp-server":  { to: "setup-server" },
  "connect-claude":    { to: "setup-connect" },
  // setup-fabric keeps its name (already prefixed)
};

// terraforming + natural-landmarks are replaced by hand-written terrain-shape /
// terrain-landmark; we preserve their reference/ libraries into the new dirs and
// remove the old ones.
const REPLACED = {
  terraforming:       "terrain-shape",
  "natural-landmarks": "terrain-landmark",
};

function setFrontmatter(text, key, value) {
  const fm = /^---\r?\n([\s\S]*?)\r?\n---\r?\n/.exec(text);
  if (!fm) return text;
  let block = fm[1];
  const line = `${key}: ${value}`;
  const re = new RegExp(`^${key}:.*$`, "m");
  block = re.test(block) ? block.replace(re, line) : block + `\n${line}`;
  return text.slice(0, fm.index) + `---\n${block}\n---\n` + text.slice(fm.index + fm[0].length);
}

function migrate(from, spec) {
  const src = join(skills, from);
  if (!existsSync(src)) { console.log(`skip ${from} (gone)`); return; }
  const dst = join(skills, spec.to);
  console.log(`${from} -> ${spec.to}  [model:${spec.model || "—"} ${spec.context || "inline"}]`);
  if (!apply) return;
  cpSync(src, dst, { recursive: true });
  const skillMd = join(dst, "SKILL.md");
  let text = readFileSync(skillMd, "utf8");
  text = setFrontmatter(text, "name", spec.to);
  if (spec.model) text = setFrontmatter(text, "model", spec.model);
  if (spec.context) text = setFrontmatter(text, "context", spec.context);
  else text = text.replace(/^context:.*\r?\n/m, "");      // ensure inline (no context)
  writeFileSync(skillMd, text);
  rmSync(src, { recursive: true, force: true });
}

console.log(apply ? "=== APPLYING ===" : "=== DRY RUN (pass --apply) ===");
for (const [from, spec] of Object.entries(MAP)) migrate(from, spec);

// replaced skills: preserve reference/ into the new hand-written dir, remove old
for (const [from, to] of Object.entries(REPLACED)) {
  const src = join(skills, from);
  if (!existsSync(src)) { console.log(`skip ${from} (gone)`); continue; }
  console.log(`${from} -> ${to}  [replaced; preserve reference/]`);
  if (!apply) continue;
  const ref = join(src, "reference");
  if (existsSync(ref)) {
    const dstRef = join(skills, to, "reference");
    if (!existsSync(dstRef)) mkdirSync(dstRef, { recursive: true });
    for (const f of readdirSync(ref)) {
      const target = join(dstRef, f);
      if (!existsSync(target)) cpSync(join(ref, f), target, { recursive: true });
    }
  }
  rmSync(src, { recursive: true, force: true });
}
console.log("done.");
