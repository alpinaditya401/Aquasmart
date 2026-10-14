// The accessibility layer of the design system. It carries no class names on purpose:
// semantics and appearance are changed for different reasons and by different people,
// and a restyle must not be able to drop an aria attribute by accident.

type FieldState = { hint?: string; error?: string }

// The ids Field renders its hint and error with. Kept here rather than in the JSX so
// the producer and the consumer of the id can never disagree.
export function hintId(id: string): string {
  return `${id}-hint`
}

export function errorId(id: string): string {
  return `${id}-error`
}

function describedBy(id: string, hint?: string, error?: string): string | undefined {
  const ids = [hint ? hintId(id) : null, error ? errorId(id) : null].filter(Boolean)
  return ids.length ? ids.join(" ") : undefined
}

// Everything a native control needs to be announced correctly: its id, whether it is
// invalid, and what describes it. Spread it onto the input, select or textarea so the
// three stay in step at every one of the call sites.
export function fieldProps(id: string, { hint, error }: FieldState = {}) {
  return {
    id,
    "aria-invalid": error ? (true as const) : undefined,
    "aria-describedby": describedBy(id, hint, error),
  }
}
