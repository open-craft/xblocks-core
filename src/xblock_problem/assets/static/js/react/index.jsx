/**
 * PROTOTYPE ONLY (throwaway branch `prototype/problem-paragon-roundtrip`).
 *
 * React + Paragon renderer for one single-select CAPA problem shape, mounted in
 * the existing LMS unit iframe by the existing xblocks-core ProblemBlock.
 *
 * It renders server-derived structured state only; it never parses widget HTML.
 * Submitting still goes through the real `xmodule_handler` -> CAPA grading path
 * and the reply is the structured view, not server-rendered UI.
 *
 * Not implemented on purpose (legacy UI still owns these): Save, Show answer,
 * hints, file/multi-input problems, and every other problem type (those fall
 * back to the legacy renderer before the learner acts).
 */
import React, { useCallback, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Alert, Button, Card, Form,
} from '@openedx/paragon';
import '@openedx/paragon/dist/light.css';
import '@openedx/paragon/dist/core.css';
import './problem-react.css';

const KNOWN_SUCCESS = ['correct', 'incorrect', 'submitted', 'partially-correct'];

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

function ProblemApp({ initialView }) {
  const [view, setView] = useState(initialView);
  const [selected, setSelected] = useState(initialView.input.value || '');
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');

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

  const submit = () => post('problem_check', { [view.input.name]: selected });
  const reset = () => post('problem_reset', {});

  const scoreText = view.score && view.score.earned !== null && view.score.possible
    ? `${view.score.earned} / ${view.score.possible}`
    : 'not shown';
  const alertVariant = STATUS_ALERT[view.status];
  const notificationMessage = view.notification && view.notification.message;

  return (
    <div className="xblock-problem-react" data-problem-status={view.status}>
      <Card>
        <Card.Body>
          <h3 className="h4 react-problem-title">{view.title}</h3>
          {/* Authored rich content, derived server-side from CAPA; never widget HTML. */}
          <div className="react-problem-prompt" dangerouslySetInnerHTML={{ __html: view.prompt_html }} />
          {view.descriptions.map((description) => (
            <div
              key={description.id}
              className="react-problem-description"
              dangerouslySetInnerHTML={{ __html: description.html }}
            />
          ))}
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
              disabled={!view.buttons.submit || Boolean(busy) || !selected}
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
