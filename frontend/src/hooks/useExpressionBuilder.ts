import { useCallback, useMemo, useState } from "react";
import {
  type ExpressionContextHint,
  validateExpressionHeuristic,
} from "../utils/expressionHeuristic";

export function useExpressionBuilder(contextHint?: ExpressionContextHint) {
  const [expression, setExpression] = useState("");
  const [, setTokenHistory] = useState<string[]>([]);

  const appendToken = useCallback((value: string) => {
    if (!value) return;
    setExpression((prev) => prev + value);
    setTokenHistory((prev) => [...prev, value]);
  }, []);

  const backspace = useCallback(() => {
    setTokenHistory((prev) => {
      if (prev.length > 0) {
        const lastToken = prev[prev.length - 1];
        setExpression((current) => current.slice(0, current.length - lastToken.length));
        return prev.slice(0, -1);
      }
      setExpression((current) => current.slice(0, -1));
      return prev;
    });
  }, []);

  const setExpressionDirect = useCallback((value: string) => {
    setExpression(value);
    setTokenHistory([]);
  }, []);

  const clear = useCallback(() => {
    setExpression("");
    setTokenHistory([]);
  }, []);

  const heuristic = useMemo(
    () => validateExpressionHeuristic(expression, contextHint),
    [expression, contextHint]
  );

  return {
    expression,
    appendToken,
    backspace,
    clear,
    setExpression: setExpressionDirect,
    heuristic,
    canUseExpression: expression.trim().length > 0,
  };
}
