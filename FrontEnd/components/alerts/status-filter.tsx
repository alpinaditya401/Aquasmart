import Link from "next/link"
import { cn } from "@/lib/utils"

const STATUSES = ["semua", "belum"] as const

export type AlertStatus = (typeof STATUSES)[number]

const STATUS_LABEL: Record<AlertStatus, string> = {
  semua: "Semua",
  belum: "Belum ditangani",
}

export function parseAlertStatus(value: string | undefined): AlertStatus {
  return value === "belum" ? "belum" : "semua"
}

// Links rather than a form: the filter works before any JavaScript loads, the server
// does the filtering, and the chosen view stays in the URL.
export function StatusFilter({ active }: { active: AlertStatus }) {
  return (
    <nav aria-label="Saring peringatan">
      <ul className="flex flex-wrap gap-2">
        {STATUSES.map((status) => {
          const selected = status === active
          return (
            <li key={status}>
              <Link
                href={`/dashboard/alerts?status=${status}`}
                aria-current={selected ? "page" : undefined}
                className={cn(
                  "inline-flex min-h-11 items-center rounded-crisp border px-3 text-sm",
                  selected
                    ? "border-deep-current bg-deep-current text-foam"
                    : "border-muted bg-surface-white text-ink hover:bg-bg-deep",
                )}
              >
                {STATUS_LABEL[status]}
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
