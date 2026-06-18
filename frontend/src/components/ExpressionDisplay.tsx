import { MathExpression } from "./MathExpression";

interface ExpressionDisplayProps {
  expression: string;
  label?: string;
  className?: string;
}

export function ExpressionDisplay({
  expression,
  label,
  className = "expression-box",
}: ExpressionDisplayProps) {
  return (
    <div>
      {label ? <p className="problem-bar-label">{label}</p> : null}
      <div className={className}>
        <MathExpression expression={expression} displayMode="block" />
      </div>
    </div>
  );
}
