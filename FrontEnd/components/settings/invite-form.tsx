"use client"

import { useRouter } from "next/navigation"
import { useState } from "react"
import { fieldProps } from "@/components/ui/a11y"
import { Field } from "@/components/ui/field"
import { button, control } from "@/components/ui/styles"
import { useCreateInvitation } from "@/hooks/use-workspace"
import { InvitationInput } from "@/lib/api/schemas"
import { fieldErrors } from "@/lib/form"
import { formatDateTime } from "@/lib/format"

const CONTACT_HINT = "Email atau nomor WA yang dipakai orang itu saat mendaftar."

// The token is returned once and is kept only in this component's state; the server
// stores a hash of it, and a token in a URL would outlive that single view.
export function InviteForm() {
  const router = useRouter()
  const invite = useCreateInvitation()
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [issued, setIssued] = useState<{ contact: string; token: string; expires_at: string }>()

  function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const parsed = InvitationInput.safeParse({ contact: new FormData(form).get("contact") })
    if (!parsed.success) {
      setErrors(fieldErrors(parsed.error))
      return
    }
    setErrors({})
    invite.mutate(parsed.data, {
      onSuccess: ({ invitation }) => {
        setIssued(invitation)
        form.reset()
        router.refresh()
      },
    })
  }

  return (
    <div className="space-y-4">
      <form onSubmit={onSubmit} noValidate className="space-y-4">
        <Field
          id="invitation-contact"
          label="Email atau nomor WA"
          hint={CONTACT_HINT}
          error={errors.contact}
        >
          <input
            name="contact"
            autoComplete="off"
            className={control()}
            {...fieldProps("invitation-contact", { hint: CONTACT_HINT, error: errors.contact })}
          />
        </Field>

        <button type="submit" disabled={invite.isPending} className={button()}>
          {invite.isPending ? "Membuat undangan..." : "Buat undangan"}
        </button>

        {invite.isError ? (
          <p role="alert" className="text-sm text-alarm-coral-text">
            {invite.error.message}
          </p>
        ) : null}
      </form>

      {issued ? (
        <div
          role="status"
          className="space-y-3 rounded-crisp border-2 border-sediment-text bg-surface-white p-4"
        >
          <p className="font-semibold text-sediment-text">Token undangan untuk {issued.contact}</p>
          <p className="select-all break-all rounded-crisp bg-bg-deep p-3 font-data text-sm text-ink">
            {issued.token}
          </p>
          <p className="text-sm text-ink">
            Berlaku 24 jam, sampai {formatDateTime(issued.expires_at)}. Kirimkan lewat jalur pribadi
            ke orangnya, jangan ke grup. Token ini tidak ditampilkan lagi setelah kotak ini ditutup.
          </p>
          <button
            type="button"
            onClick={() => setIssued(undefined)}
            className={button({ tone: "secondary" })}
          >
            Sudah dikirim, tutup
          </button>
        </div>
      ) : null}
    </div>
  )
}
