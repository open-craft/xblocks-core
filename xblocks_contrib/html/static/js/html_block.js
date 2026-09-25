/**
 * Renders a Text (HTML) XBlock inside a shadow root so that the block is styled
 * by the MFE theme without leaking styles in either direction.
 *
 * The block's HTML is rendered server-side, so there is nothing to "render"
 * here: the job is to move the existing children into a shadow root and attach
 * the theme stylesheets to it.
 */
(function () {
  'use strict';

  var CDN_CORE = 'https://cdn.jsdelivr.net/npm/@openedx/paragon@23/dist/core.min.css';

  /**
   * Fetch the Paragon theme stylesheet URLs from the MFE config API.
   *
   * Returns `core` and `theme` arrays built from PARAGON_THEME_URLS, falling back
   * to the CDN defaults for whatever the deployment does not publish. The
   * deployment's own layers are preferred over the CDN ones so there is a single
   * source of truth for theme URLs: Studio's editor reads the same key and builds
   * its preview from it, so whatever is attached here is what is previewed there.
   *
   * @param {string} mfeConfigApiUrl - URL of the MFE config API.
   * @returns {Promise<{core: string[], theme: string[]}>}
   */
  function getThemes(mfeConfigApiUrl) {
    return fetch(mfeConfigApiUrl)
      .then(function (response) { return response.json(); })
      .then(function (mfeConfig) { return mfeConfig.PARAGON_THEME_URLS || {}; })
      .catch(function (error) {
        // Not fatal: the block still renders, just with the CDN defaults.
        console.error('Text XBlock: failed to fetch theme URLs:', error);
        return {};
      })
      .then(function (themeUrls) {
        var variant = themeUrls.variants && themeUrls.variants[activeVariant(themeUrls)];
        return {
          core: [pickUrl(themeUrls.core) || CDN_CORE].filter(Boolean),
          theme: [pickUrl(variant)].filter(Boolean),
        };
      });
  }

  /**
   * Work out which variant is active.
   *
   * Two shapes are published in practice: frontend-base's `Theme`
   * (https://github.com/openedx/frontend-base/blob/main/types.ts) carries a
   * `defaults` map naming the active light and dark variants, while tutor-indigo
   * (https://github.com/overhangio/tutor-indigo) ships only a `variants` map with
   * nothing pointing at one. So read `defaults` when it is there, and otherwise
   * take the first variant present rather than dropping a configured theme.
   */
  function activeVariant(themeUrls) {
    if (themeUrls.defaults && themeUrls.defaults.light) {
      return themeUrls.defaults.light;
    }
    var variants = themeUrls.variants || {};
    if (variants.light) {
      return 'light';
    }
    var names = Object.keys(variants);
    return names.length ? names[0] : null;
  }

  /**
   * Pick the stylesheet URL out of a `core` or `variants` entry.
   *
   * Entries appear either nested (`{urls: {default, brandOverride}}`, as
   * tutor-indigo publishes) or flat (`{url}`). Prefer `brandOverride` so the
   * deployment's theme layers on top of the CDN build, and fall back to
   * `default` for configurations that publish only that.
   */
  function pickUrl(entry) {
    if (!entry) {
      return undefined;
    }
    if (entry.urls) {
      return entry.urls.brandOverride || entry.urls.default || entry.url;
    }
    return entry.url;
  }

  /**
   * Attach a stylesheet to the shadow root and, if it is not already present,
   * to the document as well.
   *
   * Some themes (including Paragon) have custom properties declared on `:root`,
   * and `:root` does not cross a shadow boundary. Attaching the theme only inside
   * the shadow root would therefore leave every custom property unresolved. The
   * stylesheets are consequently attached to the shadow root *and* to the document.
   */
  function addStylesheet(shadowRoot, url) {
    var link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = url;
    shadowRoot.appendChild(link);

    if (!document.head.querySelector('link[href="' + url + '"]')) {
      document.head.appendChild(link.cloneNode());
    }
  }

  /**
   * Move the block's server-rendered children into a shadow root.
   */
  function sandbox(element) {
    if (element.shadowRoot) {
      return element.shadowRoot.querySelector('.xblock-root');
    }

    var shadowRoot = element.attachShadow({ mode: 'open' });
    var root = document.createElement('div');
    root.classList.add('xblock-root');

    // Adopt the rendered content rather than re-rendering it, so anything the
    // server produced (images, anchors, embedded markup) is preserved as-is.
    while (element.firstChild) {
      root.appendChild(element.firstChild);
    }

    shadowRoot.appendChild(root);
    return root;
  }

  /**
   * XBlock view entry point. Invoked by the XBlock JS runtime as
   * `HtmlBlock(runtime, element, initArgs)`.
   *
   * @param {Object} runtime - XBlock runtime (unused).
   * @param {Element} element - The block's root element.
   * @param {Object} initArgs - Data supplied by `Fragment.initialize_js`.
   */
  function HtmlBlock(runtime, element, initArgs) {
    if (!initArgs || !initArgs.include_theme) {
      return;
    }

    var root = sandbox(element);

    getThemes(initArgs.mfe_config_api).then(function (themes) {
      [...themes.core, ...themes.theme].forEach(function (url) {
        addStylesheet(root.getRootNode(), url);
      });
    });
  }

  window.HtmlBlock = HtmlBlock;
}());
