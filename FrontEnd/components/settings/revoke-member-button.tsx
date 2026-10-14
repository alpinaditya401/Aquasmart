"use client"

import { useRouter } from "next/navigation"

import { useState } from "react"
import { button } from "@/components/ui/styles"
import { useConfirmFocus } from "@/hooks/use-confirm-focus"
import { useRevokeMember } from "@/hooks/use-workspace"

// Revoking is not reversible from here, so the first press only asks.
export function RevokeMemberButton({ memberId, name }: { memberId: number; name: string }) {
  const router = useRouter()
  const revoke = useRevokeMember()
  const [confirming, setConfirming] = useState(false)
  const confirmRef = useConfirmFocus(confirming)

  if (!confirming) {
    return (
      <button
        type="button"
        onClick={() => setConfirming(true)}
        className={button({ tone: "secondary" })}
        aria-label={`Cabut akses ${name}`}
      >
        Cabut akses
      </button>
    )
  }

  return (
    <fieldset
      ref={confirmRef}
      tabIndex={-1}
      aria-label={`Cabut akses ${name}?`}
      className="flex w-full flex-wrap items-center gap-2"
    >
      <p className="w-full text-sm text-ink">
        {name} kehilangan akses ke data ruang budidaya ini dan kembali mengelola ruangnya sendiri.
      </p>
      <button
        type="button"
        disabled={revoke.isPending}
        onClick={() => revoke.mutate(memberId, { onSuccess: () => router.refresh() })}
        className={button({ tone: "danger" })}
      >
        {revoke.isPending ? "Mencabut..." : "Ya, cabut akses"}
      </button>
      <button
        type="button"
        disabled={revoke.isPending}
        onClick={() => setConfirming(false)}
        className={button({ tone: "secondary" })}
      >
        Batal
      </button>
      {revoke.isError ? (
        <p role="alert" className="w-full text-sm text-alarm-coral-text">
          {revoke.error.message}
        </p>
      ) : null}
    </fieldset>
  )
}
