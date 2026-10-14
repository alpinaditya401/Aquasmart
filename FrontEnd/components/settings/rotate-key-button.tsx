"use client"

import { useRouter } from "next/navigation"

import { useState } from "react"
import { button } from "@/components/ui/styles"
import { useConfirmFocus } from "@/hooks/use-confirm-focus"
import { useRotateDeviceKey } from "@/hooks/use-devices"

// The server keeps only a hash of the key, so this state is the single place the
// plain value exists. It never goes into the URL, a query string, or storage.
export function RotateKeyButton({
  deviceId,
  deviceName,
}: {
  deviceId: string
  deviceName: string
}) {
  const router = useRouter()
  const rotate = useRotateDeviceKey(deviceId)
  const [confirming, setConfirming] = useState(false)
  const confirmRef = useConfirmFocus(confirming)
  const [issued, setIssued] = useState<{ key: string; notice: string }>()

  if (issued) {
    return (
      <div
        role="status"
        className="space-y-3 rounded-crisp border-2 border-sediment-text bg-surface-white p-4"
      >
        <p className="font-semibold text-sediment-text">Kunci baru untuk {deviceName}</p>
        <p className="select-all break-all rounded-crisp bg-bg-deep p-3 font-data text-sm text-ink">
          {issued.key}
        </p>
        <p className="text-sm text-ink">{issued.notice}</p>
        <p className="text-sm text-ink">
          Salin sekarang dan isikan ke firmware perangkat. Setelah kotak ini ditutup, nilainya tidak
          bisa ditampilkan lagi, dan satu-satunya jalan adalah menerbitkan kunci baru.
        </p>
        <button
          type="button"
          onClick={() => setIssued(undefined)}
          className={button({ tone: "secondary" })}
        >
          Sudah disalin, tutup
        </button>
      </div>
    )
  }

  if (!confirming) {
    return (
      <button
        type="button"
        onClick={() => setConfirming(true)}
        className={button({ tone: "secondary" })}
      >
        Terbitkan ulang kunci perangkat
      </button>
    )
  }

  return (
    <fieldset
      ref={confirmRef}
      tabIndex={-1}
      aria-label={`Terbitkan ulang kunci ${deviceName}?`}
      className="space-y-3 rounded-crisp border border-muted p-4"
    >
      <p className="text-sm text-ink">
        Kunci lama langsung tidak berlaku. Server menolak kiriman perangkat sampai kunci baru
        diisikan ke firmware, dan kunci baru hanya ditampilkan satu kali.
      </p>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={rotate.isPending}
          onClick={() =>
            rotate.mutate(undefined, {
              onSuccess: (result) => {
                setIssued({ key: result.device_key, notice: result.notice })
                setConfirming(false)
                router.refresh()
              },
            })
          }
          className={button({ tone: "danger" })}
        >
          {rotate.isPending ? "Menerbitkan..." : "Ya, terbitkan ulang"}
        </button>
        <button
          type="button"
          disabled={rotate.isPending}
          onClick={() => setConfirming(false)}
          className={button({ tone: "secondary" })}
        >
          Batal
        </button>
      </div>
      {rotate.isError ? (
        <p role="alert" className="text-sm text-alarm-coral-text">
          {rotate.error.message}
        </p>
      ) : null}
    </fieldset>
  )
}
