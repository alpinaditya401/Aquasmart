import { TableRegion } from "@/components/ui/table-region"
import type { Reading } from "@/lib/api/schemas"
import { formatDateTime, formatNumber, provenanceLabel } from "@/lib/format"

// Newest first: the question on this screen is "what is the water doing now".
export function ReadingsTable({ readings }: { readings: Reading[] }) {
  const rows = [...readings].reverse()
  return (
    <TableRegion label="Riwayat pembacaan, geser untuk melihat semua kolom">
      <table className="w-full min-w-[36rem] text-left text-sm">
        <thead className="bg-bg-deep text-ink">
          <tr>
            <th scope="col" className="px-4 py-3 font-semibold">
              Waktu
            </th>
            <th scope="col" className="px-4 py-3 font-semibold">
              pH
            </th>
            <th scope="col" className="px-4 py-3 font-semibold">
              Suhu (°C)
            </th>
            <th scope="col" className="px-4 py-3 font-semibold">
              Kekeruhan (NTU)
            </th>
            <th scope="col" className="px-4 py-3 font-semibold">
              Sumber
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((reading) => (
            <tr key={reading.time} className="border-t border-foam-line">
              <td className="px-4 py-3 text-muted">{formatDateTime(reading.time)}</td>
              <td className="px-4 py-3 font-data">{formatNumber(reading.ph, 1)}</td>
              <td className="px-4 py-3 font-data">{formatNumber(reading.temperature, 1)}</td>
              <td className="px-4 py-3 font-data">{formatNumber(reading.turbidity, 0)}</td>
              <td className="px-4 py-3 text-xs text-muted">
                {provenanceLabel(reading.provenance)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </TableRegion>
  )
}
