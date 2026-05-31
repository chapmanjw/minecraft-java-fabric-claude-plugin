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
    // skip loose files in skills/ (e.g. TAXONOMY.md) — only skill dirs count
    if (name.endsWith(".md") || !statSync(dir).isDirectory()) continue;
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
    // --- prefixed-namespace + tier rules (0.9.0 three-tier model) ---
    const PREFIXES = ["setup-", "survey-", "build-", "terrain-", "design-",
                      "system-", "exec-"];
    if (!PREFIXES.some((p) => name.startsWith(p))) {
      fail(`${rel}: skill "${name}" lacks a namespace prefix (${PREFIXES.join(", ")})`);
    }
    // Tier-2 orchestrators (build-*) must run inline (no context: fork) on opus
    if (name.startsWith("build-")) {
      const ctx = fmValue(fm, "context");
      if (ctx === "fork") {
        fail(`${rel}: Tier-2 orchestrator "${name}" must be inline, not context: fork`);
      }
      const model = fmValue(fm, "model");
      if (model && model !== "opus") {
        fail(`${rel}: Tier-2 orchestrator "${name}" should be model: opus (got "${model}")`);
      }
    }
    // terrain authoring/landmark leaves must link the shared terrain core,
    // not carry a duplicated method copy
    if (["terrain-shape", "terrain-landmark", "terrain-ecology",
         "terrain-integrate", "terrain-cave"].includes(name)) {
      const body = readFileSync(join(root, rel), "utf8");
      if (!body.includes("reference/terrain/")) {
        fail(`${rel}: terrain leaf "${name}" must link reference/terrain/ (shared core)`);
      }
    }
  }
}

// --- taxonomy + reference cores ---
if (!existsSync(join(root, "skills/TAXONOMY.md"))) {
  fail("missing skills/TAXONOMY.md (the 28-skill taxonomy)");
}
for (const core of ["reference/orchestration/workflow-spine.md",
                    "reference/orchestration/coherence.md",
                    "reference/terrain/method.md",
                    "reference/terrain/toolkit-api.md"]) {
  if (!existsSync(join(root, core))) fail(`missing shared reference core: ${core}`);
}

// --- live skill folder set (used by the deep checks below) ---
const skillFolders = existsSync(skillsDir)
  ? readdirSync(skillsDir).filter(
      (n) => !n.endsWith(".md") && statSync(join(skillsDir, n)).isDirectory()
    )
  : [];
const skillSet = new Set(skillFolders);

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
    // agent `skills:` entries must resolve to real skill folders (the
    // minecraft-mcp-setup breakage the rename left behind)
    const sm = /^skills:\s*\n((?:[ \t]*-[ \t]*.+\r?\n?)+)/m.exec(fm);
    if (sm) {
      for (const line of sm[1].split(/\r?\n/)) {
        const e = /^[ \t]*-[ \t]*(.+?)\s*$/.exec(line);
        if (e && !skillSet.has(e[1])) {
          fail(`${rel}: skills: entry "${e[1]}" is not an existing skill folder`);
        }
      }
    }
  }
}

// --- deep checks: reference-link resolution + deleted-name rejection ---
// These are the checks whose absence let the 0.9.0 rename ship with stale skill
// bodies, dead links, and a broken setup agent while still reporting "valid".
const OLD_NAMES = [
  "surveyor", "researcher", "planner", "blueprinter", "worker", "inspector",
  "philosopher", "terraforming", "natural-landmarks", "integrator", "player-house",
  "village-planner", "city-planner", "building-architect", "monument-builder",
  "landscape-architect", "transit-architect", "engineer", "install-mcp-mod",
  "setup-mcp-server", "connect-claude",
];
function walkMd(dir, acc) {
  if (!existsSync(dir)) return acc;
  for (const e of readdirSync(dir)) {
    const p = join(dir, e);
    if (statSync(p).isDirectory()) walkMd(p, acc);
    else if (e.endsWith(".md")) acc.push(p);
  }
  return acc;
}
const docFiles = [
  ...walkMd(skillsDir, []),
  ...walkMd(join(root, "reference"), []),
  ...walkMd(agentsDir, []),
  ...["README.md", "CLAUDE.md"].map((f) => join(root, f)).filter(existsSync),
];
const relOf = (abs) => abs.slice(root.length + 1).replace(/\\/g, "/");
const stripFences = (t) => t.replace(/```[\s\S]*?```/g, ""); // drop code examples
// matches ${CLAUDE_PLUGIN_ROOT}/<path>, reference|tools|skills|agents/<path>, and <skill>/reference/<path>
const PATH_RE =
  /(?:\$\{CLAUDE_PLUGIN_ROOT\}\/)?((?:reference|tools|skills|agents)\/[A-Za-z0-9_./-]+\.(?:md|py|json|txt)|[a-z][a-z0-9-]+\/reference\/[A-Za-z0-9_./-]+\.md)/g;
for (const abs of docFiles) {
  const rel = relOf(abs);
  const text = stripFences(readFileSync(abs, "utf8"));
  // (a) every reference path must resolve to a real file
  const seen = new Set();
  let m;
  while ((m = PATH_RE.exec(text)) !== null) {
    const token = m[1];
    if (seen.has(token)) continue;
    seen.add(token);
    // a link may be root-relative (${CLAUDE_PLUGIN_ROOT}/... or a shared
    // reference/ path), skill-local (a bare `reference/X.md` inside a SKILL.md),
    // or a bare `<skill>/reference/X.md`. Pass if it resolves under ANY of these.
    const candidates = [join(root, token), join(root, "skills", token)];
    const segs = rel.split("/");
    if (segs[0] === "skills" && segs.length > 2) {
      candidates.push(join(root, "skills", segs[1], token)); // skill-local
    }
    if (!candidates.some(existsSync)) {
      fail(`${rel}: dead reference link "${m[0]}" (resolves to nothing)`);
    }
  }
  // (b) reject deleted skill names in unambiguous skill-reference forms only
  // (backtick-wrapped, path prefix, invocation id, or "the <x> skill")
  for (const old of OLD_NAMES) {
    const forms = [
      "`" + old + "`",
      "(?<![\\w-])" + old + "/reference/",
      "skills/" + old + "/",
      "minecraft-java:" + old + "\\b",
      "\\bthe " + old + " skill\\b",
    ];
    if (forms.some((src) => new RegExp(src).test(text))) {
      fail(`${rel}: references deleted skill name "${old}" (renamed in 0.9.0)`);
    }
  }
}

// --- taxonomy bijection: every live skill appears in TAXONOMY.md ---
const taxPath = join(root, "skills/TAXONOMY.md");
if (existsSync(taxPath)) {
  const tax = readFileSync(taxPath, "utf8");
  for (const s of skillFolders) {
    if (!new RegExp("\\b" + s + "\\b").test(tax)) {
      fail(`skills/TAXONOMY.md: missing skill "${s}"`);
    }
  }
}

// --- report ---
if (errors.length) {
  console.error(`✗ validation failed (${errors.length}):`);
  for (const e of errors) console.error(`  - ${e}`);
  process.exit(1);
}
console.log("✓ plugin, marketplace, skills, and agents are valid");
