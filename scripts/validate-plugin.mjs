#!/usr/bin/env node
// Validates the plugin without external dependencies. Run: node scripts/validate-plugin.mjs
import { readdirSync, readFileSync, existsSync, statSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const errors = [];
const fail = (msg) => errors.push(msg);

/** Parse and return a JSON file, recording an error on failure. */
function readJson(rel) {
  const path = join(root, rel);
  if (!existsSync(path)) return fail(`missing file: ${rel}`), null;
  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch (e) {
    return fail(`${rel}: invalid JSON — ${e.message}`), null;
  }
}

/** Extract the YAML frontmatter block of a Markdown file, or null. */
function frontmatter(rel) {
  const text = readFileSync(join(root, rel), "utf8");
  const m = /^---\r?\n([\s\S]*?)\r?\n---\r?\n/.exec(text);
  if (!m) return fail(`${rel}: missing YAML frontmatter`), null;
  return m[1];
}

/** Read a top-level scalar key from a frontmatter block. */
function fmValue(block, key) {
  const m = new RegExp(`^${key}:\\s*(.*)$`, "m").exec(block);
  return m ? m[1].trim() : null;
}

// --- plugin manifest ---
const plugin = readJson(".claude-plugin/plugin.json");
if (plugin) {
  for (const k of ["name", "version", "description"]) {
    if (!plugin[k]) fail(`plugin.json: missing required field "${k}"`);
  }
}

// --- marketplace manifest ---
const market = readJson(".claude-plugin/marketplace.json");
if (market) {
  if (!market.name) fail(`marketplace.json: missing "name"`);
  if (!market.owner?.name) fail(`marketplace.json: missing "owner.name"`);
  if (!Array.isArray(market.plugins) || market.plugins.length === 0) {
    fail(`marketplace.json: "plugins" must be a non-empty array`);
  }
}

// --- .mcp.json.example ---
readJson(".mcp.json.example");

// --- skills ---
const skillsDir = join(root, "skills");
if (!existsSync(skillsDir)) {
  fail("missing skills/ directory");
} else {
  for (const name of readdirSync(skillsDir)) {
    const dir = join(skillsDir, name);
    if (!statSync(dir).isDirectory()) continue;
    const rel = `skills/${name}/SKILL.md`;
    if (!existsSync(join(root, rel))) {
      fail(`${rel}: missing SKILL.md`);
      continue;
    }
    const fm = frontmatter(rel);
    if (!fm) continue;
    const skillName = fmValue(fm, "name");
    if (!skillName) fail(`${rel}: frontmatter missing "name"`);
    else if (skillName !== name) {
      fail(`${rel}: name "${skillName}" does not match folder "${name}"`);
    }
    if (!fmValue(fm, "description")) {
      fail(`${rel}: frontmatter missing "description"`);
    }
  }
}

// --- agents ---
const agentsDir = join(root, "agents");
if (existsSync(agentsDir)) {
  for (const file of readdirSync(agentsDir)) {
    if (!file.endsWith(".md")) continue;
    const rel = `agents/${file}`;
    const fm = frontmatter(rel);
    if (!fm) continue;
    if (!fmValue(fm, "name")) fail(`${rel}: frontmatter missing "name"`);
    if (!fmValue(fm, "description")) fail(`${rel}: frontmatter missing "description"`);
  }
}

// --- report ---
if (errors.length) {
  console.error(`✗ validation failed (${errors.length}):`);
  for (const e of errors) console.error(`  - ${e}`);
  process.exit(1);
}
console.log("✓ plugin, marketplace, skills, and agents are valid");
