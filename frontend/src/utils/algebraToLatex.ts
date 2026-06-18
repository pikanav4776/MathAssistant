function readExponent(s: string, start: number): { exp: string; next: number } {
  if (start >= s.length) return { exp: "", next: start };

  if (s[start] === "(") {
    let depth = 0;
    for (let i = start; i < s.length; i++) {
      if (s[i] === "(") depth++;
      else if (s[i] === ")") {
        depth--;
        if (depth === 0) {
          return { exp: s.slice(start + 1, i), next: i + 1 };
        }
      }
    }
    return { exp: s.slice(start + 1), next: s.length };
  }

  let end = start;
  while (end < s.length && /[0-9a-zA-Z]/.test(s[end])) end++;
  return { exp: s.slice(start, end), next: end };
}

function popBase(out: string[]): string {
  if (out.length === 0) return "";

  if (out[out.length - 1] === ")") {
    let depth = 0;
    let start = out.length - 1;
    while (start >= 0) {
      const ch = out[start];
      if (ch === ")") depth++;
      else if (ch === "(") {
        depth--;
        if (depth === 0) break;
      }
      start--;
    }
    const base = out.splice(start).join("");
    return base;
  }

  const last = out.pop()!;
  if (/[0-9a-zA-Z]/.test(last)) {
    let base = last;
    while (out.length > 0 && /[0-9a-zA-Z]/.test(out[out.length - 1]!)) {
      base = out.pop()! + base;
    }
    return base;
  }

  return last;
}

function convertExponents(expression: string): string {
  const out: string[] = [];
  let i = 0;

  while (i < expression.length) {
    if (expression[i] === "^") {
      const base = popBase(out);
      i++;
      const { exp, next } = readExponent(expression, i);
      out.push(`${base}^{${exp}}`);
      i = next;
      continue;
    }

    out.push(expression[i]!);
    i++;
  }

  return out.join("");
}

/** Convert keyboard algebra to LaTeX for KaTeX display only. */
export function algebraToLatex(expression: string): string {
  if (!expression) return "";
  return convertExponents(expression).replace(/\*/g, " \\cdot ");
}
