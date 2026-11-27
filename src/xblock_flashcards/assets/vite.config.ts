import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
import { createRequire } from 'module';
import { dirname, join, resolve } from 'path';
import { pathToFileURL } from 'url';

const require = createRequire(import.meta.url);

// Custom Sass importer for the webpack-style `~package/path` imports used by
// Paragon's SCSS. The package is located with Node's resolution, since npm
// workspaces hoist dependencies to the repository root.
const tildeImporter = {
  findFileUrl(url: string) {
    if (!url.startsWith('~')) {
      return null;
    }
    const path = url.substring(1);
    const segments = path.split('/');
    const packageName = segments
      .slice(0, path.startsWith('@') ? 2 : 1)
      .join('/');
    const packageDir = dirname(require.resolve(`${packageName}/package.json`));
    return pathToFileURL(join(packageDir, path.substring(packageName.length)));
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
        // Paragon and Bootstrap's SCSS use deprecated Sass features.
        quietDeps: true,
        silenceDeprecations: ['import', 'global-builtin'],
      },
    },
    lightningcss: {
      errorRecovery: true, // Otherwise lightningcss fails with var() usage in media queries.
    },
  },
}));
