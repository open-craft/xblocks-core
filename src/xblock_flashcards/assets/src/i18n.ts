import messages from './messages.ts';

/**
 * The block's JavaScript translation catalog.
 *
 * The platform compiles it from the block's `.po` files (see
 * `scripts/extract-translations.ts`), and the XBlock adds it to the page, as
 * `window.XBlockFlashcardsI18N` (the XBlock's `i18n_js_namespace`).
 */
export interface JsI18nCatalog {
  gettext: (msgid: string) => string;
}

declare global {
  interface Window {
    XBlockFlashcardsI18N?: JsI18nCatalog;
  }
}

/**
 * Return the react-intl messages, translated with the catalog when there is one.
 *
 * The catalog is keyed by each message's `defaultMessage`, which `gettext`
 * returns unchanged when it has no translation.
 */
export const getMessages = (
  catalog: JsI18nCatalog | undefined = window.XBlockFlashcardsI18N,
): Record<string, string> =>
  Object.fromEntries(
    Object.values(messages).map(({ id, defaultMessage }) => [
      id,
      catalog ? catalog.gettext(defaultMessage) : defaultMessage,
    ]),
  );
