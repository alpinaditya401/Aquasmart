import { TableRegion, td, th } from "@/components/ui/table-region"
import type { Report } from "@/lib/api/schemas"
import { formatDate, formatNumber } from "@/lib/format"

// Only days that actually have samples arrive in groups, so an absent date means no
// reading was stored that day, not a zero.
export function ReportTable({ groups }: { groups: Report["groups"] }) {
  return (
    <>
      <TableRegion label="Rekap harian, geser untuk melihat semua kolom">
        <table className="w-full min-w-[44rem] text-left text-sm">
          <thead className="bg-bg-deep text-ink">
            <tr>
              <th scope="col" className={th}>
                Tanggal (UTC)
              </th>
              <th scope="col" className={th}>
                Sampel
              </th>
              <th scope="col" className={th}>
                pH rata-rata
              </th>
              <th scope="col" className={th}>
                Suhu rata-rata (°C)
              </th>
              <th scope="col" className={th}>
                Kekeruhan rata-rata (NTU)
              </th>
              <th scope="col" className={th}>
                Sampel simulasi
              </th>
            </tr>
          </thead>
          <tbody>
            {groups.map((group) => (
              <tr key={group.day} className="border-t border-foam-line">
                <td className={`${td} text-muted`}>{formatDate(group.day)}</td>
                <td className={`${td} font-data`}>{formatNumber(group.cnt, 0)}</td>
                <td className={`${td} font-data`}>{formatNumber(group.ph_avg, 1)}</td>
                <td className={`${td} font-data`}>{formatNumber(group.temperature_avg, 1)}</td>
                <td className={`${td} font-data`}>{formatNumber(group.turbidity_avg, 0)}</td>
                <td className={`${td} font-data`}>{formatNumber(group.simulation_samples, 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableRegion>
      <p className="text-xs text-muted">
        Rata-rata dihitung dari semua sampel hari itu tanpa memisahkan sumbernya, jadi satu angka
        bisa mencampur data simulasi, data seed, dan kiriman perangkat. Angka ini bukan hasil
        pengukuran yang terkalibrasi. Kolom Sampel simulasi menunjukkan berapa banyak dari kolom
        Sampel yang ditandai simulasi.
      </p>
    </>
  )
}
