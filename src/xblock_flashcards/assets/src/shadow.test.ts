import { describe, expect, it } from 'vitest';
import {
  ROOT_CLASS,
  createShadowContainer,
  createShadowStyleSheet,
  scopeSelector,
} from './shadow';

describe('scopeSelector', () => {
  it.each([
    [':root', ':host'],
    ['html', ':host'],
    ['body', `.${ROOT_CLASS}`],
    ['html, body', `:host, .${ROOT_CLASS}`],
    ['body > .modal', `.${ROOT_CLASS} > .modal`],
    [':root:not(.x)', ':host:not(.x)'],
  ])('rewrites %j to %j', (selector, expected) => {
    expect(scopeSelector(selector)).toBe(expected);
  });

  it.each([
    '.text-body',
    '.toast-body',
    '.pgn__scrollable-body::before',
    '.btn',
    '[data-body]',
    '.html',
  ])('leaves %j untouched', (selector) => {
    expect(scopeSelector(selector)).toBe(selector);
  });
});

describe('createShadowStyleSheet', () => {
  it('scopes document level rules, including nested ones', () => {
    const sheet = createShadowStyleSheet(
      ':root{--pgn-color:red} body{margin:0} @media (min-width:1px){body .btn{color:blue}}',
    );
    const [root, body, media] = Array.from(sheet.cssRules);

    expect((root as CSSStyleRule).selectorText).toBe(':host');
    expect((body as CSSStyleRule).selectorText).toBe(`.${ROOT_CLASS}`);
    expect(
      ((media as CSSMediaRule).cssRules[0] as CSSStyleRule).selectorText,
    ).toBe(`.${ROOT_CLASS} .btn`);
  });
});

describe('createShadowContainer', () => {
  it('renders into a container inside the host shadow root', () => {
    const host = document.createElement('div');
    document.body.appendChild(host);

    const container = createShadowContainer(host);

    expect(host.shadowRoot).not.toBeNull();
    expect(container.parentNode).toBe(host.shadowRoot);
    expect(container.className).toBe(ROOT_CLASS);
    // Paragon and the block styles.
    expect(host.shadowRoot!.adoptedStyleSheets).toHaveLength(2);
    expect(host.childNodes).toHaveLength(0);
  });
});
