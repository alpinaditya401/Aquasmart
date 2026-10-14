"use client"

import { useRouter } from "next/navigation"

import { useState } from "react"
import { button } from "@/components/ui/styles"
import { useConfirmFocus } from "@/hooks/use-confirm-focus"
import { useDeleteSchedule } from "@/hooks/use-schedules"

// Deleting cannot be undone, so the first press only asks; the second one deletes.
export function DeleteScheduleButton({
  deviceId,
  scheduleId,
  time,
}: {
  deviceId: string
  scheduleId: number
  time: string
}) {
  const router = useRouter()
  const remove = useDeleteSchedule(deviceId)
  const [confirming, setConfirming] = useState(false)
  const confirmRef = useConfirmFocus(confirming)

  if (!confirming) {
    return (
      <button
        type="button"
        onClick={() => setConfirming(true)}
        className={button({ tone: "secondary" })}
        aria-label={`Hapus jadwal ${time}`}
      >
        Hapus
      </button>
    )
  }

  return (
    <fieldset
      ref={confirmRef}
      tabIndex={-1}
      className="flex flex-wrap items-center gap-2"
      aria-label={`Hapus jadwal ${time}?`}
    >
      <button
        type="button"
        disabled={remove.isPending}
        onClick={() => remove.mutate(scheduleId, { onSuccess: () => router.refresh() })}
        className={button({ tone: "danger" })}
      >
        {remove.isPending ? "Menghapus..." : `Ya, hapus ${time}`}
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
