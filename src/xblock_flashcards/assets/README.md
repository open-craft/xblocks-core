# Flashcards XBlock frontend

The React + Paragon student view of the Flashcards XBlock.

The bundle is built with Vite in library mode from `src/main.tsx`, which exports
`renderBlock(runtime, element, { data, locale })`. The XBlock's `student_view`
loads `static/js/render.js`, which dynamically imports the built bundle and
calls `renderBlock` with the block's data.

`renderBlock` renders the app inside a shadow root attached to the block's
element (see `src/shadow.ts`), so Paragon styles the block without affecting the
LMS / Studio page around it:

- Paragon's CSS is built from its SCSS sources in `src/paragon.scss`, which
  includes only the components and utilities the block uses. When using
  another Paragon component, add its styles there, or it will be unstyled.
- Selectors written for a whole document are rewritten for the shadow root:
  `:root` and `html` become `:host`, `body` becomes the block's root element.
- The block's own styles live in `src/styles.scss` and are imported with
  `?inline`.
- Overlays such as tooltips must be rendered into the block (e.g.
  with the `container` prop) rather than `document.body`, or they are unstyled.

## Development

```sh
npm install
npm run build   # type-checks and writes the bundle to ../public/flashcards.js
npm run build:watch  # type-checks and rebuilds the bundle on every change
npm test        # runs the vitest suite
npm run lint    # oxlint
npm run format  # oxfmt
```

The build output in `../public/` is git-ignored similar to other NPM workspaces.

## Translations

The frontend uses react-intl, with all messages defined in `src/messages.ts`.
The Open edX translation pipeline for XBlocks only extracts gettext calls from
Python and JavaScript files, so the messages travel through it as follows:

1. `npm run i18n_extract` extracts the messages with formatjs, and writes each
   one as a `gettext("<defaultMessage>")` call in `i18n/messages.js`, with its
   `description` as a translator comment. That file is never run or bundled.
   Run the script after changing any message, and commit the result: a test
   fails when the file is out of date.
2. The repository's `make extract_translations` extracts the strings from
   `i18n/messages.js` like any other JavaScript file, into the block's
   `django.po`, which is translated with the rest of the block's strings.
3. The platform compiles the translations into a JavaScript catalog, which the
   XBlock adds to the page as `window.XBlockFlashcardsI18N`.
4. `src/i18n.ts` translates each message by looking up its `defaultMessage` in
   that catalog, and passes the result to react-intl's `IntlProvider`.

Define new messages in `src/messages.ts`: messages defined elsewhere are not
translated at runtime, and a test fails if there are any.
