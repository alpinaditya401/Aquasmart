import Link from "next/link"
import { heading, inlineLink, panel } from "@/components/ui/styles"
import { Provenance, type Report } from "@/lib/api/schemas"
import { formatDate, formatNumber, provenanceLabel } from "@/lib/format"

// The window is computed in UTC by the backend, so its edges are printed as calendar
// dates without converting them to WIB; converting would move the boundary a day.
function windowText(report: Report): string {
  const start = formatDate(report.start_at.slice(0, 10))
  const end = formatDate(report.end_at_exclusive.slice(0, 10))
  return `${start} sampai sebelum ${end} (UTC)`
}

export function ReportSummary({ report }: { report: Report }) {
  if (report.total_samples === 0) {
    return (
      <div className={`${panel()} space-y-2`}>
        <p className={heading({ level: "panel", tone: "ink" })}>
          Tidak ada pembacaan pada periode ini
        </p>
        <p className="text-sm text-ink">
          Rentang {windowText(report)} tidak memuat satu pun pembacaan untuk perangkat ini, jadi
          tidak ada rata-rata yang bisa dihitung. Pilih tanggal atau periode lain di filter di atas.
        </p>
        <Link
          href={`/dashboard?device=${encodeURIComponent(report.device_id)}`}
          className={inlineLink}
        >
          Periksa status perangkat di halaman Kualitas Air
        </Link>
      </div>
    )
  }

  return (
    <div className={`${panel()} space-y-4`}>
      <div>
        <p className="font-data text-3xl font-bold text-deep-current">
          {formatNumber(report.total_samples, 0)}
        </p>
        <p className="text-sm text-ink">pembacaan tercatat pada rentang {windowText(report)}.</p>
      </div>

      <dl className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-crisp border border-foam-line p-3">
          <dt className="text-sm text-muted">Ditandai simulasi</dt>
          <dd className="font-data text-xl text-ink">
            {formatNumber(report.simulation_samples, 0)}
          </dd>
        </div>
        <div className="rounded-crisp border border-foam-line p-3">
          <dt className="text-sm text-muted">Tidak ditandai simulasi</dt>
          <dd className="font-data text-xl text-ink">
            {formatNumber(report.non_simulation_samples, 0)}
          </dd>
        </div>
      </dl>

      <p className="text-sm text-ink">
        Sampel tanpa tanda simulasi hanya berarti pengirimnya tidak menandainya sebagai simulasi.
        Itu bukan bukti bahwa angkanya berasal dari sensor fisik yang sudah dikalibrasi.
      </p>

      <div>
        <h3 className={heading({ level: "sub", tone: "ink" })}>Rincian sumber data</h3>
        <ul className="mt-2">
          {Provenance.options.map((source) => (
            <li
              key={source}
              className="flex flex-wrap justify-between gap-2 border-t border-foam-line py-2 text-sm"
            >
              <span className="text-ink">{provenanceLabel(source)}</span>
              <span className="font-data text-ink">
                {formatNumber(report.source_counts[source], 0)}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
