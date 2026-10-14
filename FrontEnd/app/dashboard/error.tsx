"use client"

import { button, heading } from "@/components/ui/styles"

// Error boundaries must be Client Components in the App Router. The message comes
// from ApiError (already Indonesian) or ContractError, which names the endpoint.
export default function DashboardError({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div role="alert" className="rounded-panel border border-alarm-coral-text bg-surface-white p-6">
      <h1 className={heading({ level: "panel", tone: "danger" })}>Data belum bisa dimuat</h1>
      <p className="mt-2 text-sm text-ink">{error.message}</p>
      <p className="mt-1 text-sm text-muted">
        Periksa koneksi ke server, lalu coba lagi. Kalau masalah berlanjut, catat pesan di atas.
      </p>
      <button type="button" className={button({ className: "mt-4" })} onClick={reset}>
        Coba lagi
      </button>
    </div>
  )
}
