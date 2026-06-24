import { useEffect, useRef, useState } from "react";
import { fetchCalculatorAnswer } from "../api/client";
import { useExpressionBuilder } from "../hooks/useExpressionBuilder";
import type { ExpressionContextHint } from "../utils/expressionHeuristic";
import { getKeypadRowsForContext, type ExpressionToken } from "../utils/expressionTokens";
import { friendlyErrorMessage } from "../utils/friendlyErrorMessage";
import "../styles/calculator.css";

export interface CalculatorPanelProps {
  onUseExpression: (expression: string) => void;
  contextHint?: ExpressionContextHint;
  disabled?: boolean;
}

const SCOPE_NOTES: Record<ExpressionContextHint, string> = {
  problem:
    "Equations and functions supported: evaluation, composition, inverses, exponentials, and logarithms. Comparisons, sqrt, and mod are not supported.",
  step:
    "Build one algebra step for this problem. The tutor validates against the canonical path (sqrt/mod keys are for notation only).",
};

function TokenButton({
  token,
  onPress,
  disabled,
}: {
  token: ExpressionToken;
  onPress: (value: string) => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      className="calc-btn"
      aria-label={token.ariaLabel ?? token.label}
      title={token.title}
      disabled={disabled}
      onClick={() => onPress(token.value)}
    >
      {token.label}
    </button>
  );
}

function KeypadRow({
  tokens,
  onPress,
  disabled,
}: {
  tokens: ExpressionToken[];
  onPress: (value: string) => void;
  disabled?: boolean;
}) {
  return (
    <div className="calc-row">
      {tokens.map((token) => (
        <TokenButton
          key={`${token.label}-${token.value}`}
          token={token}
          onPress={onPress}
          disabled={disabled}
        />
      ))}
    </div>
  );
}

export function CalculatorPanel({
  onUseExpression,
  contextHint = "problem",
  disabled = false,
}: CalculatorPanelProps) {
  const [keyboardEnabled, setKeyboardEnabled] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [answerLoading, setAnswerLoading] = useState(false);
  const [answerError, setAnswerError] = useState<string | null>(null);
  const keyboardInputRef = useRef<HTMLInputElement>(null);
  const {
    expression,
    appendToken,
    backspace,
    clear,
    setExpression,
    heuristic,
    canUseExpression,
  } = useExpressionBuilder(contextHint);

  const keypadRows = getKeypadRowsForContext(contextHint);

  useEffect(() => {
    if (keyboardEnabled) {
      keyboardInputRef.current?.focus();
    }
  }, [keyboardEnabled]);

  useEffect(() => {
    setAnswer(null);
    setAnswerError(null);
  }, [expression]);

  const showValidationError = expression.length > 0 && !heuristic.isValid;
  const showValidationWarning =
    expression.length > 0 && heuristic.isValid && heuristic.warnings.length > 0;

  const previewClass = [
    "calc-preview",
    showValidationError ? "calc-preview--invalid" : "",
    showValidationWarning ? "calc-preview--warning" : "",
    keyboardEnabled ? "calc-preview--keyboard" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const handleUseExpression = () => {
    const trimmed = expression.trim();
    if (!trimmed || disabled || !heuristic.isValid) return;
    onUseExpression(trimmed);
    clear();
  };

  const handleAppend = (value: string) => {
    if (disabled) return;
    appendToken(value);
  };

  const handleKeyboardToggle = () => {
    setKeyboardEnabled((enabled) => !enabled);
  };

  const handleAnswer = async () => {
    const trimmed = expression.trim();
    if (!trimmed || disabled || answerLoading) return;

    setAnswerLoading(true);
    setAnswerError(null);
    try {
      const result = await fetchCalculatorAnswer(trimmed);
      setAnswer(result.answer);
    } catch (err) {
      setAnswer(null);
      setAnswerError(friendlyErrorMessage(err));
    } finally {
      setAnswerLoading(false);
    }
  };

  return (
    <section className="calculator-panel" aria-label="Expression calculator">
      <div className="calc-preview-header">
        <label className="calc-preview-label" htmlFor={`calc-preview-${contextHint}`}>
          Enter Expression
        </label>
        <button
          type="button"
          className={
            keyboardEnabled
              ? "calc-btn calc-keyboard-toggle calc-keyboard-toggle--active"
              : "calc-btn calc-keyboard-toggle"
          }
          aria-pressed={keyboardEnabled}
          disabled={disabled}
          onClick={handleKeyboardToggle}
        >
          {keyboardEnabled ? "Keyboard on" : "Use keyboard"}
        </button>
      </div>

      {keyboardEnabled ? (
        <input
          ref={keyboardInputRef}
          id={`calc-preview-${contextHint}`}
          type="text"
          className={previewClass}
          value={expression}
          onChange={(event) => setExpression(event.target.value)}
          disabled={disabled}
          autoComplete="off"
          spellCheck={false}
          aria-live="polite"
        />
      ) : (
        <div
          id={`calc-preview-${contextHint}`}
          className={previewClass}
          aria-live="polite"
        >
          {expression || <span className="calc-preview__placeholder"> </span>}
        </div>
      )}

      {answer ? (
        <p className="calc-answer" aria-live="polite">
          Answer: {answer}
        </p>
      ) : null}

      {answerLoading ? <p className="calc-answer calc-answer--loading">Computing answer...</p> : null}

      {answerError ? <p className="calc-feedback calc-feedback--error">{answerError}</p> : null}

      <p className="calc-scope-note">{SCOPE_NOTES[contextHint]}</p>

      {showValidationError ? (
        <p className="calc-feedback calc-feedback--error">{heuristic.errors[0]}</p>
      ) : null}

      {showValidationWarning ? (
        <p className="calc-feedback calc-feedback--warning">{heuristic.warnings[0]}</p>
      ) : null}

      <div className="calc-row calc-row--controls">
        <button
          type="button"
          className="calc-btn"
          aria-label="Clear"
          disabled={disabled}
          onClick={clear}
        >
          C
        </button>
        <button
          type="button"
          className="calc-btn"
          aria-label="Backspace"
          disabled={disabled}
          onClick={backspace}
        >
          ⌫
        </button>
        <button
          type="button"
          className="calc-btn calc-ans-btn"
          aria-label="Answer"
          title="Answer"
          disabled={!canUseExpression || disabled || answerLoading}
          onClick={handleAnswer}
        >
          Ans
        </button>
      </div>

      {keypadRows.map((row, index) => (
        <KeypadRow
          key={`row-${index}`}
          tokens={row}
          onPress={handleAppend}
          disabled={disabled}
        />
      ))}

      <button
        type="button"
        className="calc-btn calc-use-btn"
        disabled={!canUseExpression || disabled || !heuristic.isValid}
        onClick={handleUseExpression}
      >
        Use Expression
      </button>
    </section>
  );
}
