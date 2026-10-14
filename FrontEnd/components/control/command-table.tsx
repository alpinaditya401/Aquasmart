import { statusText } from "@/components/ui/styles"
import { TableRegion, td, th } from "@/components/ui/table-region"
import type { Command } from "@/lib/api/schemas"
import { formatEpoch, provenanceLabel } from "@/lib/format"

export const ACTUATOR_LABEL: Record<Command["actuator"], string> = {
  aerator: "Aerator",
  feeder: "Feeder",
  pump: "Pompa",
}

export const STATUS_LABEL: Record<Command["status"], string> = {
  pending: "Antre",
  delivered: "Terkirim",
  succeeded: "Berhasil",
  failed: "Gagal",
  timeout: "Tanpa balasan",
}

const STATUS_TONE = {
  pending: "neutral",
  delivered: "neutral",
  succeeded: "ok",
  failed: "danger",
  timeout: "warning",
} as const satisfies Record<Command["status"], "neutral" | "ok" | "danger" | "warning">

export function commandAction(command: Command): string {
  if (command.actuator === "feeder") return `Pakan ${command.duration} detik`
  return command.value ? "Nyalakan" : "Matikan"
}

// The server already returns the newest command first.
export function CommandTable({ commands }: { commands: Command[] }) {
  return (
    <TableRegion label="Riwayat perintah, geser untuk melihat semua kolom">
      <table className="w-full min-w-[40rem] text-left text-sm">
        <thead className="bg-bg-deep text-ink">
          <tr>
            <th scope="col" className={th}>
              Waktu
            </th>
            <th scope="col" className={th}>
              Aktuator
            </th>
            <th scope="col" className={th}>
              Perintah
            </th>
            <th scope="col" className={th}>
              Status
            </th>
            <th scope="col" className={th}>
              Sumber
            </th>
          </tr>
        </thead>
        <tbody>
          {commands.map((command) => (
            <tr key={command.id} className="border-t border-foam-line">
              <td className={`${td} text-muted`}>{formatEpoch(command.created_at)}</td>
              <td className={td}>{ACTUATOR_LABEL[command.actuator]}</td>
              <td className={td}>{commandAction(command)}</td>
              <td className={`${td} ${statusText({ tone: STATUS_TONE[command.status] })}`}>
                {STATUS_LABEL[command.status]}
              </td>
              <td className={`${td} text-xs text-muted`}>{provenanceLabel(command.provenance)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </TableRegion>
  )
}
