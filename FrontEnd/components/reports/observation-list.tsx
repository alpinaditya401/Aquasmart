import { DeleteObservationButton } from "@/components/reports/delete-observation-button"
import { panel } from "@/components/ui/styles"
import type { Observation } from "@/lib/api/schemas"
import { formatDate, formatDateTime, formatNumber, provenanceLabel } from "@/lib/format"

export function ObservationList({
  observations,
  isAdmin,
}: {
  observations: Observation[]
  isAdmin: boolean
}) {
  if (observations.length === 0) {
    return (
      <p className={`${panel()} text-sm text-muted`}>
        Belum ada observasi untuk perangkat ini.{" "}
        {isAdmin
          ? "Catat sampel pertama lewat formulir di bawah."
          : "Akun viewer tidak bisa mencatat observasi. Minta admin ruang budidaya menambahkannya."}
      </p>
    )
  }

  return (
    <ul className="divide-y divide-foam-line rounded-panel border border-foam-line bg-surface-white">
      {observations.map((observation) => {
        const observed = formatDate(observation.observed_at)
        const measured: string[] = []
        if (observation.weight_g !== null) {
          measured.push(`Berat ${formatNumber(observation.weight_g, 1)} gram`)
        }
        if (observation.length_cm !== null) {
          measured.push(`Panjang ${formatNumber(observation.length_cm, 1)} cm`)
        }

        return (
          <li
            key={observation.id}
            className="flex flex-wrap items-start justify-between gap-3 px-4 py-3 sm:px-6"
          >
            <div className="space-y-1">
              <p className="font-semibold text-ink">{observed}</p>
              {measured.length > 0 ? (
                <p className="font-data text-sm text-ink">{measured.join(", ")}</p>
              ) : null}
              {observation.notes ? <p className="text-sm text-ink">{observation.notes}</p> : null}
              <p className="text-xs text-muted">
                Dicatat {formatDateTime(observation.created_at)}, sumber{" "}
                {provenanceLabel(observation.provenance)}.
              </p>
            </div>
            {isAdmin ? (
              <DeleteObservationButton observationId={observation.id} observedLabel={observed} />
            ) : null}
          </li>
        )
      })}
    </ul>
  )
}
