import type { z } from "zod"
import { button, inlineLink } from "@/components/ui/styles"
import { ExportKind, type ReportQuery } from "@/lib/api/schemas"

// One label per kind that /api/export accepts. Keyed by the schema enum, so a kind
// added to the contract fails to compile here instead of quietly disappearing.
const KIND_LABEL: Record<z.output<typeof ExportKind>, string> = {
  readings: "Pembacaan sensor",
  alerts: "Peringatan",
  commands: "Perintah aktuator",
  feeding_logs: "Riwayat perintah pakan (berhasil, gagal, timeout)",
  reports: "Rekap harian",
  telemetry: "Telemetri mentah",
}

function exportHref(
  query: ReportQuery,
  kind: z.output<typeof ExportKind>,
  format: "csv" | "json",
): string {
  return `/api/export?${new URLSearchParams({ ...query, kind, format }).toString()}`
}

// Plain links, not fetch: the download goes through the BFF at /api/*, which forwards
// the Content-Disposition header from PHP unchanged.
export function ExportLinks({ query }: { query: ReportQuery }) {
  return (
    <>
      <ul className="divide-y divide-foam-line rounded-panel border border-foam-line bg-surface-white">
        {ExportKind.options.map((kind) => (
          <li
            key={kind}
            className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6"
          >
            <span className="text-sm font-medium text-ink">{KIND_LABEL[kind]}</span>
            <span className="flex flex-wrap items-center gap-3">
              <a
                href={exportHref(query, kind, "csv")}
                className={button({ tone: "secondary" })}
                aria-label={`Unduh CSV ${KIND_LABEL[kind]}`}
              >
                CSV
              </a>
              <a
                href={exportHref(query, kind, "json")}
                className={inlineLink}
                aria-label={`Buka JSON ${KIND_LABEL[kind]}`}
              >
                JSON
              </a>
            </span>
          </li>
        ))}
      </ul>
      <p className="text-sm text-muted">
        Unduhan memakai filter yang sedang aktif di atas. CSV turun sebagai berkas, JSON terbuka di
        tab browser. Server menolak ekspor yang melebihi 10.000 baris dan meminta periode yang lebih
        pendek. Ekspor perintah aktuator dan perintah pakan berisi perintah simulasi beserta
        statusnya, bukan bukti bahwa alat fisik bergerak.
      </p>
    </>
  )
}
