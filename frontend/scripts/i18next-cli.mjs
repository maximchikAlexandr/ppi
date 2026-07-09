import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import { dirname, extname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));
const projectRoot = dirname(root);
const sourceRoot = join(projectRoot, "src");
const localesRoot = join(sourceRoot, "locales");
const localeFile = (language) => join(localesRoot, language, "translation.json");

async function listSourceFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const nested = await Promise.all(
    entries.map(async (entry) => {
      const path = join(directory, entry.name);
      if (entry.isDirectory()) {
        if (entry.name === "locales") {
          return [];
        }
        return listSourceFiles(path);
      }
      return [".ts", ".tsx"].includes(extname(entry.name)) ? [path] : [];
    }),
  );
  return nested.flat();
}

async function readJson(path) {
  try {
    return JSON.parse(await readFile(path, "utf-8"));
  } catch {
    return {};
  }
}

function collectKeys(source, path) {
  const keys = new Map();
  // Three call shapes are recognised:
  //   1. t("ns.key", "fallback")
  //   2. t("ns.key")               -> no fallback (extracted with empty string)
  //   3. t(`ns.prefix.${var}`)     -> static prefix registered as a prefix
  //      key (e.g. ns.prefix.) so dynamic dispatches stay type-safe even
  //      when the extractor cannot see the runtime value.
  const re1 = /\bt\(\s*["']([^"']+)["']\s*,\s*["']([^"']*)["']/g;
  const re2 = /\bt\(\s*["']([a-z][^"']+)["']\s*\)/g;
  const re3 = /\bt\(\s*`([a-z][^`$]*?)\.\$\{[^}]+\}`/g;
  for (const match of source.matchAll(re1)) {
    const [, key, fallback] = match;
    if (keys.has(key) && keys.get(key) !== fallback) {
      throw new Error(`Duplicate i18n key with different fallback: ${key} in ${relative(projectRoot, path)}`);
    }
    keys.set(key, fallback);
  }
  for (const match of source.matchAll(re2)) {
    const [, key] = match;
    if (!keys.has(key)) {
      keys.set(key, "");
    }
  }
  for (const match of source.matchAll(re3)) {
    const [, prefix] = match;
    if (!keys.has(prefix)) {
      keys.set(prefix, "");
    }
  }
  return keys;
}

function sortedObject(entries) {
  return Object.fromEntries([...entries].sort(([left], [right]) => left.localeCompare(right)));
}

async function extract() {
  const files = await listSourceFiles(sourceRoot);
  const extracted = new Map();
  for (const file of files) {
    const keys = collectKeys(await readFile(file, "utf-8"), file);
    for (const [key, fallback] of keys) {
      if (extracted.has(key) && extracted.get(key) !== fallback) {
        throw new Error(`Duplicate i18n key with different fallback: ${key}`);
      }
      extracted.set(key, fallback);
    }
  }

  const previousRu = await readJson(localeFile("ru"));
  const enEntries = [...extracted].map(([key, fallback]) => [key, fallback]);
  const ruEntries = [...extracted].map(([key, fallback]) => [key, previousRu[key] ?? fallback]);

  const newEn = `${JSON.stringify(sortedObject(enEntries), null, 2)}\n`;
  const newRu = `${JSON.stringify(sortedObject(ruEntries), null, 2)}\n`;

  if (process.argv[3] === "--check") {
    const oldEn = await readFile(localeFile("en"), "utf-8").catch(() => "");
    const oldRu = await readFile(localeFile("ru"), "utf-8").catch(() => "");
    if (oldEn !== newEn || oldRu !== newRu) {
      console.error("ERROR: locale files are out of sync with extracted keys.");
      console.error("Run 'npm run i18n:extract' (or 'make i18n-freshness' with autocommit) to update them.");
      process.exit(1);
    }
    console.log(`OK: ${extracted.size} keys, locale files in sync.`);
    return;
  }

  await mkdir(dirname(localeFile("en")), { recursive: true });
  await mkdir(dirname(localeFile("ru")), { recursive: true });
  await writeFile(localeFile("en"), newEn);
  await writeFile(localeFile("ru"), newRu);
  console.log(`Extracted ${extracted.size} keys to src/locales/{en,ru}/translation.json`);
}

const command = process.argv[2];
if (command !== "extract") {
  console.error("Usage: i18next-cli extract [--check]");
  process.exit(1);
}

await extract();
