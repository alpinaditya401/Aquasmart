"use client"

import { useRouter } from "next/navigation"
import { useState } from "react"
import { fieldProps } from "@/components/ui/a11y"
import { Field } from "@/components/ui/field"
import { button, control } from "@/components/ui/styles"
import { useAcceptInvitation } from "@/hooks/use-workspace"
import { InvitationAcceptInput } from "@/lib/api/schemas"
import { fieldErrors } from "@/lib/form"

const TOKEN_HINT = "64 karakter, hanya angka dan huruf a sampai f."

export function JoinWorkspaceForm() {
  const router = useRouter()
  const accept = useAcceptInvitation()
  const [errors, setErrors] = useState<Record<string, string>>({})

  function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const parsed = InvitationAcceptInput.safeParse({ token: data.get("token") })
    if (!parsed.success) {
      setErrors(fieldErrors(parsed.error))
      return
    }
    setErrors({})
    // The role changes on the server, so the page has to be rendered again to show
    // what this account may still do.
    accept.mutate(parsed.data, { onSuccess: () => router.refresh() })
  }

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-4">
      <Field id="invitation-token" label="Token undangan" hint={TOKEN_HINT} error={errors.token}>
        <input
          name="token"
          autoComplete="off"
          spellCheck={false}
          className={`${control({ font: "data" })}`}
          {...fieldProps("invitation-token", { hint: TOKEN_HINT, error: errors.token })}
        />
      </Field>

      <button type="submit" disabled={accept.isPending} className={button()}>
        {accept.isPending ? "Memeriksa token..." : "Gabung ke ruang budidaya"}
      </button>

      {accept.isError ? (
        <p role="alert" className="text-sm text-alarm-coral-text">
          {accept.error.message}
        </p>
      ) : null}
      {accept.isSuccess ? (
        <p role="status" className="text-sm text-ink">
          Undangan diterima. Peran akun ini sekarang viewer dengan akses baca.
        </p>
      ) : null}
    </form>
  )
}
