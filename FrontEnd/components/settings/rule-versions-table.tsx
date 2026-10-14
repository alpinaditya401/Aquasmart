import type { z } from "zod"
import { TableRegion, td, th } from "@/components/ui/table-region"
import type { RuleVersion } from "@/lib/api/schemas"
import { formatDateTime, formatNumber } from "@/lib/format"

// The full id is a 64 character SHA-256; the row shows the opening characters so the
// table still fits, and the column header says how many.
const ID_PREFIX_LENGTH = 12

export function RuleVersionsTable({ versions }: { versions: z.output<typeof RuleVersion>[] }) {
  return (
    <TableRegion label="Versi aturan, geser untuk melihat semua kolom">
      <table className="w-full min-w-[52rem] text-left text-sm">
        <thead className="bg-bg-deep text-ink">
          <tr>
            <th scope="col" className={th}>
              Dicatat
            </th>
            <th scope="col" className={th}>
              Versi
            </th>
            <th scope="col" className={th}>
              pH
            </th>
            <th scope="col" className={th}>
              Suhu (°C)
            </th>
            <th scope="col" className={th}>
              Kekeruhan maks (NTU)
            </th>
            <th scope="col" className={th}>
              Pembacaan
            </th>
            <th scope="col" className={th}>
              Awal id snapshot ({ID_PREFIX_LENGTH} karakter)
            </th>
          </tr>
        </thead>
        <tbody>
          {versions.map((version) => (
            <tr key={version.id} className="border-t border-foam-line">
              <td className={`${td} text-muted`}>{formatDateTime(version.created_at)}</td>
              <td className={`${td} font-data`}>{version.version}</td>
              <td className={`${td} font-data`}>
                {formatNumber(version.config.ph_min, 1)} sampai{" "}
                {formatNumber(version.config.ph_max, 1)}
              </td>
              <td className={`${td} font-data`}>
                {formatNumber(version.config.temperature_min, 1)} sampai{" "}
                {formatNumber(version.config.temperature_max, 1)}
              </td>
              <td className={`${td} font-data`}>{formatNumber(version.config.turbidity_max, 0)}</td>
              <td className={`${td} font-data`}>{version.reading_count}</td>
              <td className={`${td} font-data text-xs text-muted`}>
                {version.id.slice(0, ID_PREFIX_LENGTH)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </TableRegion>
  )
}
