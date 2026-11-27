/**
 * Renders the block inside a shadow root styled with Paragon, without any of
 * Paragon's global styles (reboot, typography, utilities) reaching the host
 * LMS / Studio page.
 *
 * Paragon's CSS is written for a whole document: its design tokens are CSS
 * variables declared on `:root`, and its base typography is set on `html` and
 * `body`. None of those match inside a shadow root, so each stylesheet is
 * parsed with the browser's CSSOM and those selectors are rewritten to target
 * the shadow host and the block's root element instead. The resulting
 * constructable stylesheets are adopted by the shadow root, and are shared by
 * every flashcards block on the page.
 */
import paragonStyles from './paragon.scss?inline';
import blockStyles from './styles.scss?inline';

/** Class of the element inside the shadow root that React renders into. */
export const ROOT_CLASS = 'xblock-root';

/**
 * Rewrites a selector written for a document so that it applies inside a
 * shadow root: `:root` and `html` become `:host`, `body` becomes the element
 * React renders into.
 */
export const scopeSelector = (selector: string): string =>
  selector
    .replace(/:root(?![\w-])/g, ':host')
    .replace(/(^|[\s,>+~(])html(?![\w-])/g, '$1:host')
    .replace(/(^|[\s,>+~(])body(?![\w-])/g, `$1.${ROOT_CLASS}`);

const scopeRules = (rules: CSSRuleList) => {
  for (const rule of Array.from(rules)) {
    if (rule instanceof CSSStyleRule) {
      const scoped = scopeSelector(rule.selectorText);
      if (scoped !== rule.selectorText) {
        rule.selectorText = scoped;
      }
    }
    // Recurse into @media, @supports, @layer and nested style rules.
    if ('cssRules' in rule) {
      scopeRules((rule as CSSGroupingRule).cssRules);
    }
  }
};

/** Parses `css` into a stylesheet scoped for use inside a shadow root. */
export const createShadowStyleSheet = (css: string): CSSStyleSheet => {
  const sheet = new CSSStyleSheet();
  // `replaceSync` ignores @import, which is not allowed in constructed sheets.
  sheet.replaceSync(css);
  scopeRules(sheet.cssRules);
  return sheet;
};

let sheets: CSSStyleSheet[] | undefined;

/**
 * Returns the block's stylesheets, in cascade order: Paragon (see
 * `paragon.scss`) and the block's own styles. They are created
 * once and shared by every flashcards block on the page.
 */
const getStyleSheets = () =>
  (sheets ??= [paragonStyles, blockStyles].map(createShadowStyleSheet));

/**
 * Attaches a styled shadow root to `host` and returns the element to render
 * the block into.
 */
export const createShadowContainer = (host: Element): HTMLElement => {
  const shadowRoot = host.shadowRoot ?? host.attachShadow({ mode: 'open' });
  shadowRoot.adoptedStyleSheets = getStyleSheets();
  const container = document.createElement('div');
  container.className = ROOT_CLASS;
  shadowRoot.replaceChildren(container);
  return container;
};
