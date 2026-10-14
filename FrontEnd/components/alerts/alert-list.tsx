import { statusText } from "@/components/ui/styles"
import type { Alert } from "@/lib/api/schemas"
import { formatDateTime } from "@/lib/format"
import { AcknowledgeButton } from "./acknowledge-button"

const SEVERITY_LABEL: Record<Alert["severity"], string> = {
  info: "Info",
  warning: "Perhatian",
  critical: "Kritis",
}

// Colour only repeats what the label already says, so a reader who cannot separate
// these hues still gets the severity from the word. The hues themselves come from the
// shared statusText variant, so a severity and a command status never drift apart.
const SEVERITY_TONE = {
  info: "neutral",
  warning: "warning",
  critical: "danger",
} as const satisfies Record<Alert["severity"], "neutral" | "warning" | "danger">

function handledText(alert: Alert): string {
  if (!alert.acknowledged) return "Belum ditangani"
  return alert.acknowledged_at
    ? `Sudah ditangani ${formatDateTime(alert.acknowledged_at)}`
    : "Sudah ditangani, waktu penanganannya tidak tercatat"
}

// A list, not a table: the message is a full sentence and would force a wide table to
// scroll sideways on a phone. The server sends the newest alert first; keep that order.
export function AlertList({
  alerts,
  deviceNames,
  canAcknowledge,
}: {
  alerts: Alert[]
  deviceNames: ReadonlyMap<string, string>
  canAcknowledge: boolean
}) {
  return (
    <ul className="divide-y divide-foam-line rounded-panel border border-foam-line bg-surface-white">
      {alerts.map((alert) => {
        const device = deviceNames.get(alert.device_id) ?? alert.device_id
        const raised = formatDateTime(alert.created_at)
        return (
          <li key={alert.id} className="space-y-2 px-4 py-4 sm:px-6">
            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <span className={statusText({ tone: SEVERITY_TONE[alert.severity] })}>
                {SEVERITY_LABEL[alert.severity]}
              </span>
              {/* Device ids are a single token of up to 128 characters, which only
                  break-all can wrap; break-words leaves them overflowing on a phone. */}
              <span className="min-w-0 break-all text-sm text-ink">{device}</span>
              <span className="text-sm text-muted">{raised}</span>
            </div>
            <p className="break-words text-ink">{alert.message}</p>
            <p className="text-xs text-muted">Sumber: {alert.source}</p>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-ink">{handledText(alert)}</p>
              {canAcknowledge && !alert.acknowledged ? (
                <AcknowledgeButton
                  alertId={alert.id}
                  label={`${SEVERITY_LABEL[alert.severity]}, ${device}, ${raised}`}
                />
              ) : null}
            </div>
          </li>
        )
      })}
    </ul>
  )
}
