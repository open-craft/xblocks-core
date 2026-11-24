/**
 * PROTOTYPE ONLY (throwaway branch `prototype/problem-paragon-numeric`).
 *
 * React + Paragon renderer for one single-select CAPA problem shape and one
 * Studio-basic numerical input shape, mounted in the existing LMS unit iframe by
 * the existing xblocks-core ProblemBlock.
 *
 * It renders server-derived structured state only; it never parses widget HTML.
 * Submitting still goes through the real `xmodule_handler` -> CAPA grading path
 * and the reply is the structured view, not server-rendered UI.
 *
 * The numerical input reuses the existing CAPA `preview_formcalc` handler (via
 * `input_ajax`) and the MathJax runtime the LMS already loads into the problem
 * iframe; it does not reimplement formula parsing or MathJax.
 *
 * Not implemented on purpose (legacy UI still owns these): Save, Show answer,
 * hints, file/multi-input problems, and every other problem type (those fall
 * back to the legacy renderer before the learner acts).
 */
import React, {
  useCallback, useEffect, useRef, useState,
} from 'react';
import { createRoot } from 'react-dom/client';
import {
  Alert, Button, Card, Form,
} from '@openedx/paragon';
import '@openedx/paragon/dist/light.css';
import '@openedx/paragon/dist/core.css';
import './problem-react.css';

const KNOWN_SUCCESS = ['correct', 'incorrect', 'submitted', 'partially-correct'];
const PREVIEW_DELAY_MS = 300;

const STATUS_ALERT = {
  correct: 'success',
  incorrect: 'danger',
  'partially-correct': 'warning',
  submitted: 'info',
};

const STATUS_TEXT = {
  correct: 'Correct',
  incorrect: 'Incorrect',
  'partially-correct': 'Partially correct',
  submitted: 'Submitted (correctness withheld)',
  unsubmitted: 'Not submitted yet',
};

const readCsrfToken = () => {
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : '';
};

const attemptsText = (attempts) => {
  if (!attempts || !attempts.used) {
    return 'No graded attempts yet.';
  }
  const plural = attempts.used === 1 ? 'attempt' : 'attempts';
  if (!attempts.allowed) {
    return `${attempts.used} graded ${plural} used (unlimited attempts allowed).`;
  }
  return `${attempts.used} of ${attempts.allowed} attempts used.`;
};

/**
 * Typeset one element with the MathJax runtime the LMS provides in this iframe.
 * Same readiness contract the legacy renderer uses (MathJax v3/v4).
 */
const typeset = (element, latex) => {
  if (!element) {
    return;
  }
  const mathJax = window.MathJax;
  if (mathJax && mathJax.startup && mathJax.startup.promise) {
    mathJax.startup.promise.then(() => {
      mathJax.typesetClear([element]);
      element.textContent = `\\(${latex || ''}\\)`;
      return mathJax.typesetPromise([element]);
    }).catch((error) => {
      console.log('[ProblemReactDisplay] MathJax error:', error);
    });
  } else {
    element.textContent = latex ? `\\(${latex}\\)` : '';
  }
};

const typesetHtml = (element) => {
  if (!element) {
    return;
  }
  const mathJax = window.MathJax;
  if (mathJax && mathJax.startup && mathJax.startup.promise) {
    mathJax.startup.promise.then(() => mathJax.typesetPromise([element])).catch((error) => {
      console.log('[ProblemReactDisplay] MathJax error:', error);
    });
  }
};

function ProblemApp({ initialView }) {
  const [view, setView] = useState(initialView);
  const [selected, setSelected] = useState(initialView.input.value || '');
  const [answer, setAnswer] = useState(initialView.input.value || '');
  const [preview, setPreview] = useState({ latex: '', error: '' });
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const promptRef = useRef(null);
  const previewRef = useRef(null);
  const lastSentRef = useRef(0);
  const visiblePreviewRef = useRef(0);

  // Authored prompt may contain MathJax delimiters; the LMS already loads MathJax.
  useEffect(() => {
    typesetHtml(promptRef.current);
  }, [view.prompt_html, view.status]);

  const requestPreview = useCallback((formula) => {
    if (!view.input.preview) {
      return;
    }
    const sentAt = Date.now();
    lastSentRef.current = sentAt;
    if (!formula || !formula.trim()) {
      visiblePreviewRef.current = sentAt;
      setPreview({ latex: '', error: '' });
      return;
    }
    const body = new URLSearchParams({
      react_view: '1',
      input_id: view.input.id,
      dispatch: 'preview_formcalc',
      formula,
      request_start: String(sentAt),
    });
    fetch(view.input.preview_url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': readCsrfToken(),
      },
      body: body.toString(),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        const requestStart = data.request_start || sentAt;
        if (requestStart <= visiblePreviewRef.current) {
          return; // stale preview response
        }
        visiblePreviewRef.current = requestStart;
        setPreview({ latex: data.preview || '', error: data.error || '' });
      })
      .catch((previewError) => {
        console.log('[ProblemReactDisplay] preview failed:', previewError);
      });
  }, [view.input.preview, view.input.preview_url, view.input.id]);

  // Same ~300ms rate limit as the legacy formula preview.
  useEffect(() => {
    if (!view.input.preview) {
      return undefined;
    }
    const timeout = window.setTimeout(() => requestPreview(answer), PREVIEW_DELAY_MS);
    return () => window.clearTimeout(timeout);
  }, [answer, requestPreview, view.input.preview]);

  useEffect(() => {
    if (!view.input.preview) {
      return;
    }
    typeset(previewRef.current, preview.latex);
  }, [preview, view.input.preview]);

  const post = useCallback(async (dispatch, extraFields) => {
    setBusy(dispatch);
    setError('');
    try {
      // Dispatch is the handler URL suffix, exactly like the legacy renderer's
      // `${ajax_url}/${dispatch}` calls (xmodule_handler(suffix, POST)).
      const body = new URLSearchParams({ react_view: '1', ...extraFields });
      const response = await fetch(`${view.ajax_url}/${dispatch}`, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': readCsrfToken(),
        },
        body: body.toString(),
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      if (data.react_view) {
        setView(data.react_view);
        setSelected(data.react_view.input.value || '');
        setAnswer(data.react_view.input.value || '');
      }
      if (typeof data.success === 'string' && !KNOWN_SUCCESS.includes(data.success)) {
        setError(data.success);
      } else if (data.success === false) {
        setError(data.msg || 'CAPA rejected the action.');
      }
    } catch (requestError) {
      setError(`Request failed: ${requestError.message}`);
    } finally {
      setBusy('');
    }
  }, [view.ajax_url]);

  const submit = () => post('problem_check', { [view.input.name]: answer });
  const reset = () => post('problem_reset', {});

  const scoreText = view.score && view.score.earned !== null && view.score.possible
    ? `${view.score.earned} / ${view.score.possible}`
    : 'not shown';
  const alertVariant = STATUS_ALERT[view.status];
  const notificationMessage = view.notification && view.notification.message;
  const isNumeric = view.input.kind === 'text';

  return (
    <div className="xblock-problem-react" data-problem-status={view.status}>
      <Card>
        <Card.Body>
          <h3 className="h4 react-problem-title">{view.title}</h3>
          {/* Authored rich content, derived server-side from CAPA; never widget HTML. */}
          <div
            ref={promptRef}
            className="react-problem-prompt"
            dangerouslySetInnerHTML={{ __html: view.prompt_html }}
          />
          {view.descriptions.map((description) => (
            <div
              key={description.id}
              className="react-problem-description"
              dangerouslySetInnerHTML={{ __html: description.html }}
            />
          ))}

          {isNumeric ? (
            <Form.Group className="react-problem-numeric">
              <Form.Label htmlFor={`input_${view.input.id}`}>{view.title}</Form.Label>
              <div className="react-problem-numeric-row">
                <Form.Control
                  type="text"
                  id={`input_${view.input.id}`}
                  name={view.input.name}
                  value={answer}
                  size={view.input.size || undefined}
                  disabled={!view.buttons.submit}
                  onChange={(event) => setAnswer(event.target.value)}
                  className="react-problem-numeric-input"
                />
                {view.input.trailing_text ? (
                  <span className="react-problem-trailing-text">{view.input.trailing_text}</span>
                ) : null}
              </div>
              <div
                ref={previewRef}
                className="react-problem-preview equation"
                data-testid="react-problem-preview"
              />
              {preview.error ? (
                <p className="x-small text-danger mt-1 react-problem-preview-error">{preview.error}</p>
              ) : null}
            </Form.Group>
          ) : (
            <fieldset className="react-problem-choices">
              <legend className="h6">{view.title}</legend>
              {view.choices.map((choice) => (
                <Form.Check
                  key={choice.id}
                  type="radio"
                  id={`${view.problem_html_id}-${choice.id}`}
                  name={view.input.name}
                  value={choice.id}
                  checked={selected === choice.id}
                  disabled={!view.buttons.submit}
                  onChange={() => setSelected(choice.id)}
                  className="react-problem-choice"
                  label={(
                    <span
                      className="react-problem-choice-label"
                      dangerouslySetInnerHTML={{ __html: choice.label_html }}
                    />
                  )}
                />
              ))}
            </fieldset>
          )}

          {error && (
            <Alert variant="danger" className="mt-3 react-problem-error">
              {error}
            </Alert>
          )}
          {alertVariant && (
            <Alert variant={alertVariant} className="mt-3 react-problem-feedback">
              <strong>{STATUS_TEXT[view.status]}</strong>
              {notificationMessage ? ` — ${notificationMessage}` : ''}
              {view.message ? <div>{view.message}</div> : null}
              {view.hint ? <div className="react-problem-hint">{view.hint}</div> : null}
            </Alert>
          )}

          <div className="react-problem-state mt-3" data-testid="react-problem-state">
            <div>{attemptsText(view.attempts)}</div>
            <div>{view.grading_method ? `Grading method: ${view.grading_method}` : ''}</div>
            <div>{view.graded ? `Score: ${scoreText}` : 'Ungraded practice problem'}</div>
            {view.has_saved_answers ? <div>Saved answers are pending grading.</div> : null}
            {view.closed ? <div>This problem is closed.</div> : null}
          </div>

          <div className="react-problem-actions mt-3">
            <Button
              variant="primary"
              onClick={submit}
              disabled={!view.buttons.submit || Boolean(busy) || !(isNumeric ? answer.trim() : selected)}
            >
              {busy === 'problem_check' ? 'Submitting…' : view.buttons.submit_label}
            </Button>
            {view.buttons.reset && (
              <Button
                variant="tertiary"
                className="ml-2"
                onClick={reset}
                disabled={Boolean(busy)}
              >
                {busy === 'problem_reset' ? 'Resetting…' : 'Reset'}
              </Button>
            )}
          </div>
          {(view.buttons.save || view.buttons.show_answer) && (
            <p className="x-small text-gray-500 mt-3 react-problem-gaps">
              Prototype gap: Save / Show answer / hints stay on the legacy renderer.
            </p>
          )}
        </Card.Body>
      </Card>
    </div>
  );
}

function renderProblemReact(runtime, element, initArgs) {
  const mountPoint = element.querySelector('.xblock-problem-react');
  if (!mountPoint) {
    return;
  }
  createRoot(mountPoint).render(<ProblemApp initialView={initArgs} />);
}

window.ProblemReactRenderer = renderProblemReact;
