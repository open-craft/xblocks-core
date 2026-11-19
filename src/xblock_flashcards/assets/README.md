# Flashcards XBlock frontend

The React + Paragon student view of the Flashcards XBlock.

The bundle is built with Vite in library mode from `src/main.tsx`, which exports
`renderBlock(element, runtime, data)`. The XBlock's `student_view` loads
`static/js/render.js`, which dynamically imports the built bundle and calls
`renderBlock` with the block's `display_name`, `is_shuffled` and `cards`.

## Development

```sh
npm install
npm run dev     # serves index.html with demo data from src/demo.tsx
npm run build   # type-checks and writes the bundle to ../public/flashcards.js
npm test        # runs the vitest suite
npm run lint    # oxlint
npm run format  # oxfmt
```

The build output in `../public/` is git-ignored similar to other NPM workspaces.
