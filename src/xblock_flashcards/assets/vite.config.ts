import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
import { resolve } from 'path';
import { pathToFileURL } from 'url';

// Custom Sass importer that strips the webpack-style `~` prefix
// and resolves the import from node_modules.
const tildeImporter = {
  findFileUrl(url: string) {
    if (url.startsWith('~')) {
      const resolved = resolve(
        import.meta.dirname,
        'node_modules',
        url.substring(1),
      );
      return pathToFileURL(resolved);
    }
    return null;
  },
};

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [react()],
  define: {
    'process.env.NODE_ENV': JSON.stringify(mode),
  },
  build: {
    outDir: resolve(import.meta.dirname, '../public'),
    emptyOutDir: true,
    copyPublicDir: false,
    lib: {
      entry: resolve(import.meta.dirname, 'src/main.tsx'),
      formats: ['es'],
      fileName: 'flashcards',
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        loadPaths: [resolve(import.meta.dirname, 'node_modules')],
        importers: [tildeImporter],
        silenceDeprecations: ['import', 'global-builtin'],
      },
    },
    lightningcss: {
      errorRecovery: true, // Otherwise lightningcss fails with var() usage in media queries.
    },
  },
}));
