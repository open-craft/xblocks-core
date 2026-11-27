import { afterEach, describe, expect, it } from 'vitest';
import { getMessages } from './i18n.ts';
import messages from './messages.ts';

describe('getMessages', () => {
  afterEach(() => {
    delete window.XBlockFlashcardsI18N;
  });

  it('returns the default messages without a catalog', () => {
    expect(getMessages(undefined)).toEqual(
      Object.fromEntries(
        Object.values(messages).map((m) => [m.id, m.defaultMessage]),
      ),
    );
  });

  it('translates each message by looking up its default message', () => {
    const catalog = {
      gettext: (msgid: string) => (msgid === 'Start' ? 'Commencer' : msgid),
    };

    const translated = getMessages(catalog);

    expect(translated[messages.startBtnLabel.id]).toBe('Commencer');
    expect(translated[messages.helpLabel.id]).toBe('Help');
  });

  it('uses the catalog the platform adds to the page by default', () => {
    window.XBlockFlashcardsI18N = { gettext: (msgid: string) => `[${msgid}]` };

    expect(getMessages()[messages.startBtnLabel.id]).toBe('[Start]');
  });
});
