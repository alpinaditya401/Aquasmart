// Streaming SSR: Next.js shows this as the Suspense fallback while a page awaits its
// data. Every route under /dashboard shares it, so the shapes stay generic: a heading,
// one panel and a few rows. A skeleton shaped like one specific page would promise
// content the other pages never render.
export default function Loading() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="skeleton h-9 w-1/3" />
        <div className="skeleton h-4 w-1/2" />
      </div>

      <div className="rounded-panel border border-foam-line bg-surface-white p-6">
        <div className="skeleton h-4 w-1/2" />
        <div className="skeleton mt-3 h-3 w-2/3" />
      </div>

      <div className="space-y-2">
        {["baris-1", "baris-2", "baris-3", "baris-4"].map((row) => (
          <div key={row} className="skeleton h-12 w-full" />
        ))}
      </div>
    </div>
  )
}
