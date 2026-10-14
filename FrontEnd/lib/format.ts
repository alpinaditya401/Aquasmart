import type { z } from "zod"
import type { Provenance } from "@/lib/api/schemas"

// Server Components render once on the server, so pinning the zone keeps the output
// identical no matter where the server runs. Readings are stored in UTC.
const TIME_ZONE = "Asia/Jakarta"

const dateTime = new Intl.DateTimeFormat("id-ID", {
  timeZone: TIME_ZONE,
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
})

const dateOnly = new Intl.DateTimeFormat("id-ID", {
  timeZone: "UTC",
  day: "2-digit",
  month: "long",
  year: "numeric",
})

export function formatDateTime(iso: string): string {
  return `${dateTime.format(new Date(iso))} WIB`
}

// Command timestamps arrive as epoch seconds.
export function formatEpoch(seconds: number): string {
  return `${dateTime.format(new Date(seconds * 1000))} WIB`
}

// Calendar dates (YYYY-MM-DD) carry no zone; format them as written.
export function formatDate(ymd: string): string {
  return dateOnly.format(new Date(`${ymd}T00:00:00Z`))
}

export function formatNumber(value: number, fractionDigits: number): string {
  return new Intl.NumberFormat("id-ID", {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(value)
}

// Same wording as Provenance::label() in server/src/Provenance.php, so a label means
// the same thing in the old SPA, the API and this UI.
const PROVENANCE_LABELS: Record<z.output<typeof Provenance>, string> = {
  simulation: "SIMULASI",
  device: "DEVICE / kalibrasi belum diverifikasi",
  manual: "MANUAL",
  seed: "SEED / data contoh",
  legacy_unverified: "LEGACY / UNVERIFIED",
}

export function provenanceLabel(provenance: z.output<typeof Provenance>): string {
  return PROVENANCE_LABELS[provenance]
}
