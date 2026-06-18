import { MathExpression } from "./MathExpression";

const EXPECTED_EXPR_PATTERN =
  /(expected:\s*)([0-9a-zA-Z+\-*/^() ]+?)(?=[).,]|$)/g;

interface HintWithMathProps {
  text: string;
  className?: string;
}

/** Plain hint text with KaTeX for embedded `expected: <expr>` fragments (skip_message). */
export function HintWithMath({ text, className }: HintWithMathProps) {
  const parts: Array<string | { key: number; expr: string }> = [];
  let lastIndex = 0;
  let matchIndex = 0;

  for (const match of text.matchAll(EXPECTED_EXPR_PATTERN)) {
    const full = match[0];
    const expr = match[2]?.trim() ?? "";
    const index = match.index ?? 0;

    if (index > lastIndex) {
      parts.push(text.slice(lastIndex, index));
    }

    parts.push(match[1] ?? "expected: ");
    if (expr) {
      parts.push({ key: matchIndex++, expr });
    }

    lastIndex = index + full.length;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  if (parts.length === 0) {
    return <p className={className}>{text}</p>;
  }

  return (
    <p className={className}>
      {parts.map((part, index) =>
        typeof part === "string" ? (
          <span key={`text-${index}`}>{part}</span>
        ) : (
          <MathExpression key={`expr-${part.key}`} expression={part.expr} />
        )
      )}
    </p>
  );
}
