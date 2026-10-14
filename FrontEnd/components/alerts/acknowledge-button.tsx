"use client"

import { useRouter } from "next/navigation"
import { button } from "@/components/ui/styles"
import { useAcknowledgeAlert } from "@/hooks/use-alerts"

// Every row shows the same wording, so the accessible name repeats the severity,
// device and time that tell the rows apart.
export function AcknowledgeButton({ alertId, label }: { alertId: number; label: string }) {
  const router = useRouter()
  const acknowledge = useAcknowledgeAlert()

  // The refreshed list drops this button, so the confirmation is announced while the
  // component is still mounted; after the refresh the row itself states it is handled.
  if (acknowledge.isSuccess) {
    return (
      <p role="status" className="text-sm text-clear-water-text">
        Peringatan ditandai sudah ditangani.
      </p>
    )
  }

  return (
    <div className="space-y-2">
      <button
        type="button"
        disabled={acknowledge.isPending}
        onClick={() => acknowledge.mutate(alertId, { onSuccess: () => router.refresh() })}
        className={button({ tone: "secondary" })}
        aria-label={`Tandai sudah ditangani: ${label}`}
      >
        {acknowledge.isPending ? "Menyimpan..." : "Tandai sudah ditangani"}
      </button>
      {acknowledge.isError ? (
        <p role="alert" className="text-sm text-alarm-coral-text">
          {acknowledge.error.message}
        </p>
      ) : null}
    </div>
  )
}
