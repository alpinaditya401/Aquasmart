// Wide tables scroll inside this region instead of pushing the page sideways on a
// phone. The region takes focus so keyboard users can scroll it too.
export function TableRegion({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <section
      className="overflow-x-auto rounded-panel border border-foam-line bg-surface-white"
      // biome-ignore lint/a11y/noNoninteractiveTabindex: a horizontally scrollable region must take focus so keyboard users can scroll it.
      tabIndex={0}
      aria-label={label}
    >
      {children}
    </section>
  )
}

export const th = "px-4 py-3 font-semibold"
export const td = "px-4 py-3"
