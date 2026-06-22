import { useExpressionBuilder } from "../hooks/useExpressionBuilder";
import type { ExpressionContextHint } from "../utils/expressionHeuristic";
import { CALCULATOR_KEYPAD_ROWS, type ExpressionToken } from "../utils/expressionTokens";
import "../styles/calculator.css";

export interface CalculatorPanelProps {
  onUseExpression: (expression: string) => void;
  contextHint?: ExpressionContextHint;
  disabled?: boolean;
}

function TokenButton({
  token,
  onPress,
}: {
  token: ExpressionToken;
  onPress: (value: string) => void;
}) {
  return (
    <button
      type="button"
      className="calc-btn"
      aria-label={token.ariaLabel ?? token.label}
      title={token.title}
      onClick={() => onPress(token.value)}
    >
      {token.label}
    </button>
  );
}

function KeypadRow({
  tokens,
  onPress,
}: {
  tokens: ExpressionToken[];
  onPress: (value: string) => void;
}) {
  return (
    <div className="calc-row">
      {tokens.map((token) => (
        <TokenButton key={`${token.label}-${token.value}`} token={token} onPress={onPress} />
      ))}
    </div>
  );
}

export function CalculatorPanel({
  onUseExpression,
  contextHint,
  disabled = false,
}: CalculatorPanelProps) {
  const {
    expression,
    appendToken,
    backspace,
    clear,
    heuristic,
    canUseExpression,
  } = useExpressionBuilder(contextHint);

  const showValidationError = expression.length > 0 && !heuristic.isValid;
  const showValidationWarning =
    expression.length > 0 && heuristic.isValid && heuristic.warnings.length > 0;

  const previewClass = [
    "calc-preview",
    showValidationError ? "calc-preview--invalid" : "",
    showValidationWarning ? "calc-preview--warning" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const handleUseExpression = () => {
    const trimmed = expression.trim();
    if (!trimmed || disabled || !heuristic.isValid) return;
    onUseExpression(trimmed);
  };

  return (
    <section className="calculator-panel" aria-label="Expression calculator">
      <label className="calc-preview-label" htmlFor="calc-expression-preview">
        Enter Expression
      </label>
      <div
        id="calc-expression-preview"
        className={previewClass}
        aria-live="polite"
      >
        {expression || <span className="calc-preview__placeholder"> </span>}
      </div>

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
          onClick={clear}
        >
          C
        </button>
        <button
          type="button"
          className="calc-btn"
          aria-label="Backspace"
          onClick={backspace}
        >
          ⌫
        </button>
      </div>

      {CALCULATOR_KEYPAD_ROWS.map((row, index) => (
        <KeypadRow key={`row-${index}`} tokens={row} onPress={appendToken} />
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
