import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import messages from '../src/messages.ts';
import { JS_FILE, extractMessages, toJs } from './extract-translations.ts';

describe('extract-translations', () => {
  it('keeps i18n/messages.js up to date (run `npm run i18n_extract`)', async () => {
    expect(readFileSync(JS_FILE, 'utf8')).toBe(toJs(await extractMessages()));
  });

  it('only finds messages from src/messages.ts, which src/i18n.ts translates', async () => {
    const extractedIds = (await extractMessages()).map((m) => m.id).sort();
    const runtimeIds = Object.values(messages)
      .map((m) => m.id)
      .sort();

    expect(extractedIds).toEqual(runtimeIds);
  });

  it('renders messages as gettext calls with translator comments', () => {
    const js = toJs([
      {
        id: 'a',
        defaultMessage: 'Say "hi"\\now',
        description: 'Spans\n  two lines.',
      },
      { id: 'b', defaultMessage: 'No description' },
    ]);

    expect(js).toContain(
      '// Translators: Spans two lines.\ngettext("Say \\"hi\\"\\\\now");',
    );
    expect(js).toContain('\n\ngettext("No description");');
  });
});
