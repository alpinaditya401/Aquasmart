"use client"

import { useRouter } from "next/navigation"

import { useState } from "react"
import { button } from "@/components/ui/styles"
import { useConfirmFocus } from "@/hooks/use-confirm-focus"
import { useDeleteObservation } from "@/hooks/use-observations"

// The API has no undo for an observation, so the first press only asks and the
// second one deletes.
export function DeleteObservationButton({
  observationId,
  observedLabel,
}: {
  observationId: number
  observedLabel: string
}) {
  const router = useRouter()
  const remove = useDeleteObservation()
  const [confirming, setConfirming] = useState(false)
  const confirmRef = useConfirmFocus(confirming)

  if (!confirming) {
    return (
      <button
        type="button"
        onClick={() => setConfirming(true)}
        className={button({ tone: "secondary" })}
        aria-label={`Hapus observasi ${observedLabel}`}
      >
        Hapus
      </button>
    )
  }

  return (
    <fieldset
      className="flex flex-wrap items-center gap-2"
      ref={confirmRef}
      tabIndex={-1}
      aria-label={`Hapus observasi ${observedLabel}?`}
    >
      <button
        type="button"
        disabled={remove.isPending}
        onClick={() => remove.mutate(observationId, { onSuccess: () => router.refresh() })}
        className={button({ tone: "danger" })}
      >
        {remove.isPending ? "Menghapus..." : `Ya, hapus ${observedLabel}`}
      </button>
      <button
        type="button"
        disabled={remove.isPending}
        onClick={() => setConfirming(false)}
        className={button({ tone: "secondary" })}
      >
        Batal
      </button>
      {remove.isError ? (
        <p role="alert" className="w-full text-sm text-alarm-coral-text">
          {remove.error.message}
        </p>
      ) : null}
    </fieldset>
  )
}
