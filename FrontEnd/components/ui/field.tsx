import { errorId, hintId } from "@/components/ui/a11y"

// Label, control, hint and error wired together by id. The control itself is passed in
// so native inputs, selects and textareas all work; it should spread fieldProps(id)
// from components/ui/a11y.ts, which produces the matching aria attributes.
export function Field({
  id,
  label,
  hint,
  error,
  children,
}: {
  id: string
  label: string
  hint?: string
  error?: string
  children: React.ReactNode
}) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="block text-sm font-medium text-ink">
        {label}
      </label>
      {children}
      {hint ? (
        <p id={hintId(id)} className="text-xs text-muted">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={errorId(id)} role="alert" className="text-sm text-alarm-coral-text">
          {error}
        </p>
      ) : null}
    </div>
  )
}
