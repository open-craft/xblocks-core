# Flashcards XBlock frontend

The React + Paragon student view of the Flashcards XBlock.

The bundle is built with Vite in library mode from `src/main.tsx`, which exports
`renderBlock(runtime, element, { data })`. The XBlock's `student_view`
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
