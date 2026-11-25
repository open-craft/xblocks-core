/**
 * PROTOTYPE ONLY (throwaway branch `prototype/problem-paragon-wgu-theme`).
 *
 * Deployment theme delivery for the React problem renderer.
 *
 * The block bundles Paragon's stock `core.css` + `light.css`, so with no theme
 * configured it already renders the platform defaults at the installed Paragon
 * version. This module adds whatever the *deployment* configures on top, by
 * reading `PARAGON_THEME_URLS` from the LMS MFE config API inside the unit
 * iframe (the same endpoint the Learning MFE itself reads).
 *
 * Canonical shapes handled (frontend-platform):
 *   core.urls.default / core.urls.brandOverride
 *   defaults.<variant>          — variant *name*, e.g. { light: "light" }
 *   variants[<name>].urls.default / .brandOverride
 *   default.<variant>           — legacy singular alias, kept as a fallback
 *
 * Load order is the documented one: core default -> core brandOverride ->
 * variant default -> variant brandOverride, deduplicated. `$paragonVersion` is
 * replaced with the *installed* Paragon version (never the `^23` range), which
 * is also what the version-exact CDN fallback uses.
 *
 * Fail-soft by design: no config, a rejected fetch, non-JSON, a malformed value
 * or a partial theme all leave the bundled defaults in place, so the problem is
 * always readable and usable. No author-facing knob, no selector override.
 */
const paragonVersion = require('@openedx/paragon/package.json').version;

export const MFE_CONFIG_URL = '/api/mfe_config/v1?mfe=learning';

const cdnDefault = (file) => `https://cdn.jsdelivr.net/npm/@openedx/paragon@${paragonVersion}/dist/${file}`;

const withInstalledVersion = (url) => (
  typeof url === 'string' ? url.replace(/\$paragonVersion/g, paragonVersion).trim() : ''
);

/**
 * Variant name the deployment points at ("light" unless it says otherwise).
 */
export function variantName(themeUrls) {
  const named = themeUrls
    && ((themeUrls.defaults && themeUrls.defaults.light)
      || (themeUrls.default && themeUrls.default.light));
  return typeof named === 'string' && named.trim() ? named.trim() : 'light';
}

/**
 * Ordered, deduplicated deployment stylesheet URLs for one theme config.
 * Empty when the deployment configures no theme at all.
 */
export function themeSheets(themeUrls) {
  if (!themeUrls || typeof themeUrls !== 'object') {
    return [];
  }
  const core = (themeUrls.core && themeUrls.core.urls) || {};
  const variant = ((themeUrls.variants || {})[variantName(themeUrls)] || {});
  const variantUrls = variant.urls || {};
  const ordered = [
    // A layer the deployment leaves out falls back to the stock sheet at the
    // installed version, so a partial theme still renders every component.
    core.default || cdnDefault('core.min.css'),
    core.brandOverride,
    variantUrls.default || cdnDefault('light.min.css'),
    variantUrls.brandOverride,
  ].map(withInstalledVersion).filter(Boolean);
  return Array.from(new Set(ordered));
}

/**
 * Append the deployment stylesheets to the iframe document, skipping any that
 * are already there. Returns the URLs actually added.
 */
export function applyThemeSheets(doc, urls) {
  const added = [];
  urls.forEach((href) => {
    if (doc.querySelector(`link[rel="stylesheet"][href="${href}"]`)) {
      return;
    }
    const link = doc.createElement('link');
    link.rel = 'stylesheet';
    link.href = href;
    link.dataset.paragonThemeSource = 'deployment';
    doc.head.appendChild(link);
    added.push(href);
  });
  return added;
}

/**
 * Read the deployment's theme config and load it into this document.
 * Never rejects and never blocks the first render.
 */
export async function loadDeploymentTheme(doc = document, configUrl = MFE_CONFIG_URL) {
  try {
    const response = await fetch(configUrl, {
      credentials: 'same-origin',
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) {
      return [];
    }
    const config = await response.json();
    return applyThemeSheets(doc, themeSheets(config && config.PARAGON_THEME_URLS));
  } catch (error) {
    // Bundled platform defaults are already in place; a missing/slow/broken
    // config endpoint must not change what the learner sees or can do.
    return [];
  }
}
