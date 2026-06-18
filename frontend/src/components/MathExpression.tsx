import katex from "katex";
import { useMemo } from "react";
import { algebraToLatex } from "../utils/algebraToLatex";

interface MathExpressionProps {
  expression: string;
  displayMode?: "inline" | "block";
  className?: string;
}

export function MathExpression({
  expression,
  displayMode = "inline",
  className,
}: MathExpressionProps) {
  const rendered = useMemo(() => {
    const latex = algebraToLatex(expression);
    try {
      const html = katex.renderToString(latex, {
        throwOnError: false,
        displayMode: displayMode === "block",
        output: "html",
      });
      const hasError = html.includes('class="katex-error"');
      return hasError ? null : html;
    } catch {
      return null;
    }
  }, [expression, displayMode]);

  if (!rendered) {
    return (
      <span className={["math-fallback", className].filter(Boolean).join(" ")}>
        {expression}
      </span>
    );
  }

  return (
    <span
      className={["math-expression", className].filter(Boolean).join(" ")}
      dangerouslySetInnerHTML={{ __html: rendered }}
    />
  );
}
