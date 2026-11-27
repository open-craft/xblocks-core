/**
 * Extract the frontend's react-intl messages for the XBlock translation tools.
 *
 * The Open edX translation pipeline for XBlocks only reads gettext calls from
 * Python and JavaScript files. This script writes each message as a
 * `gettext("<defaultMessage>")` call in `i18n/messages.js`, which the
 * repository's `make extract_translations` extracts like any other JavaScript
 * file. The platform compiles the translations into a JavaScript catalog
 * (`window.XBlockFlashcardsI18N`), and at runtime `src/i18n.ts` looks up each
 * message's `defaultMessage` in that catalog.
 *
 * Run with `npm run i18n_extract`, and commit the result.
 */
import { extract, type MessageDescriptor } from '@formatjs/cli-lib';
import { globSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const assetsDir = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '..',
);

export const JS_FILE = path.join(assetsDir, 'i18n', 'messages.js');

/** Source files to extract messages from, relative to the assets directory. */
const sourceFiles = () =>
  globSync('src/**/*.{ts,tsx}', {
    cwd: assetsDir,
    exclude: (file) => /\.(test|spec)\.tsx?$|\.d\.ts$|^src\/test\//.test(file),
  }).sort();

/**
 * Extract the message descriptors from the source files, sorted by id.
 */
export const extractMessages = async (): Promise<MessageDescriptor[]> => {
  const files = sourceFiles();
  const output = await extract(
    files.map((file) => path.join(assetsDir, file)),
    {
      throws: true,
      // Keep messages exactly as written: they are looked up verbatim at runtime.
      preserveWhitespace: true,
    },
  );
  // The output is keyed by message id, and the descriptors leave the id out.
  const messages = Object.entries(
    JSON.parse(output) as Record<string, MessageDescriptor>,
  ).map(([id, message]) => ({ ...message, id }));
  for (const message of messages) {
    if (!message.defaultMessage) {
      throw new Error(`Message "${message.id}" has no defaultMessage.`);
    }
  }
  return messages.sort((a, b) => a.id.localeCompare(b.id));
};

/**
 * Render the messages as a JavaScript file of `gettext()` calls.
 *
 * The file is never run: Django's `makemessages` extracts its strings into the
 * block's `djangojs.po`. Each `defaultMessage` becomes a `msgid`, and its
 * description a translator comment.
 */
export const toJs = (messages: MessageDescriptor[]): string => {
  const lines = [
    '// Messages of the Flashcards XBlock frontend, for the translation tools.',
    '// Generated from src/ by `npm run i18n_extract`: do not edit.',
    '// This file is not run or bundled: `make extract_translations` extracts its strings.',
  ];
  for (const { defaultMessage, description } of messages) {
    lines.push('');
    if (description) {
      const text =
        typeof description === 'string'
          ? description
          : JSON.stringify(description);
      // Django only extracts comments that start with "Translators", on one line.
      lines.push(`// Translators: ${text.replace(/\s+/g, ' ').trim()}`);
    }
    lines.push(`gettext(${JSON.stringify(defaultMessage)});`);
  }
  return `${lines.join('\n')}\n`;
};

if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const messages = await extractMessages();
  writeFileSync(JS_FILE, toJs(messages));
  console.log(
    `Wrote ${messages.length} messages to ${path.relative(process.cwd(), JS_FILE)}`,
  );
}
