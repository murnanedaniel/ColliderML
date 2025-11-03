#!/usr/bin/env node
// Syncs the root CHANGELOG.md into docs and injects latest dataset entries into docs/index.md

import { readFile, writeFile, mkdir, stat, cp } from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const repoRoot = path.resolve(__dirname, '..');
const rootChangelogPath = path.join(repoRoot, 'CHANGELOG.md');
const docsDir = path.join(repoRoot, 'docs');
const docsChangelogPath = path.join(docsDir, 'changelog.md');
const docsIndexPath = path.join(docsDir, 'index.md');

const START_TAG = '<!-- CHANGELOG:DATASET:START -->';
const END_TAG = '<!-- CHANGELOG:DATASET:END -->';

async function ensureDocsDir() {
  try {
    await stat(docsDir);
  } catch {
    await mkdir(docsDir, { recursive: true });
  }
}

function extractDatasetEntries(markdown, maxCount = 5) {
  const lines = markdown.split(/\r?\n/);
  const datasetEntries = [];
  let currentVersion = '';

  const versionRegex = /^##\s+\[(.*?)\]\s*-\s*(\d{4}-\d{2}-\d{2}|Unreleased)/;
  for (const line of lines) {
    const versionMatch = line.match(versionRegex);
    if (versionMatch) {
      const versionLabel = versionMatch[1];
      const datePart = versionMatch[2];
      currentVersion = `${versionLabel} — ${datePart}`;
      continue;
    }

    // Bullet lines that contain [dataset]
    if (/^\s*-\s+/u.test(line) && /\[dataset\]/i.test(line)) {
      const cleaned = line
        .replace(/^\s*-\s+/u, '- ')
        .replace(/\s*\[dataset\]\s*/i, ' ')
        .trim();
      datasetEntries.push({ version: currentVersion, text: cleaned });
      if (datasetEntries.length >= maxCount) break;
    }
  }
  return datasetEntries;
}

function buildDetailsBlock(entries) {
  const header = '::: details Dataset Changelog (latest 5)';
  const footer = ':::';
  const linkLine = 'See the full changelog: [Changelog](/changelog).';
  if (entries.length === 0) {
    return [
      START_TAG,
      header,
      '- No dataset entries found yet.',
      linkLine,
      footer,
      END_TAG,
    ].join('\n');
  }
  const bodyLines = entries.map(e => `- ${e.version ? `(${e.version}) ` : ''}${e.text}`);
  return [START_TAG, header, ...bodyLines, linkLine, footer, END_TAG].join('\n');
}

async function main() {
  await ensureDocsDir();

  // Mirror root changelog into docs
  await cp(rootChangelogPath, docsChangelogPath, { force: true });

  // Inject latest dataset entries into docs/index.md
  const [rootChangelog, docsIndex] = await Promise.all([
    readFile(rootChangelogPath, 'utf8'),
    readFile(docsIndexPath, 'utf8').catch(() => ''),
  ]);

  const entries = extractDatasetEntries(rootChangelog, 5);
  const detailsBlock = buildDetailsBlock(entries);

  let newIndexContent = docsIndex;
  if (!docsIndex.includes(START_TAG) || !docsIndex.includes(END_TAG)) {
    // Append a new block at the end if markers are missing
    newIndexContent = [docsIndex.trimEnd(), '', detailsBlock, ''].join('\n');
  } else {
    const before = docsIndex.split(START_TAG)[0];
    const after = docsIndex.split(END_TAG)[1] ?? '';
    newIndexContent = [before.trimEnd(), detailsBlock, after.trimStart()].join('\n');
  }

  await writeFile(docsIndexPath, newIndexContent, 'utf8');
  // Also ensure the docs changelog file exists and has the content
  await writeFile(docsChangelogPath, rootChangelog, 'utf8');
}

main().catch(err => {
  console.error('[sync_changelog] Error:', err);
  process.exit(1);
});


