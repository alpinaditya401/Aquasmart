"use client"

import { useRouter } from "next/navigation"
import { useState } from "react"
import { fieldProps } from "@/components/ui/a11y"
import { Field } from "@/components/ui/field"
import { button, control } from "@/components/ui/styles"
import { useUpdateProfile } from "@/hooks/use-session"
import { ProfileInput } from "@/lib/api/schemas"
import { fieldErrors } from "@/lib/form"

const PHONE_HINT = "Nomor yang bisa dihubungi, maksimal 30 karakter."

export function ProfileForm({ name, phone }: { name: string; phone: string }) {
  const router = useRouter()
  const update = useUpdateProfile()
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [saved, setSaved] = useState<string>()

  function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const parsed = ProfileInput.safeParse({ name: data.get("name"), phone: data.get("phone") })
    // Clear both results first: otherwise a rejected submit still shows the previous
    // confirmation, or the server error from a submit before that.
    setSaved(undefined)
    update.reset()
    if (!parsed.success) {
      setErrors(fieldErrors(parsed.error))
      return
    }
    setErrors({})
    update.mutate(parsed.data, {
      // The message echoes the values the server stored, not the ones that were typed.
      onSuccess: ({ user }) => {
        setSaved(`Profil tersimpan: ${user.name}, ${user.phone}.`)
        router.refresh()
      },
    })
  }

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field id="profile-name" label="Nama lengkap" error={errors.name}>
          <input
            name="name"
            defaultValue={name}
            autoComplete="name"
            className={control()}
            {...fieldProps("profile-name", { error: errors.name })}
          />
        </Field>
        <Field id="profile-phone" label="Nomor telepon" hint={PHONE_HINT} error={errors.phone}>
          <input
            name="phone"
            type="tel"
            inputMode="tel"
            defaultValue={phone}
            autoComplete="tel"
            className={control()}
            {...fieldProps("profile-phone", { hint: PHONE_HINT, error: errors.phone })}
          />
        </Field>
      </div>

      <button type="submit" disabled={update.isPending} className={button()}>
        {update.isPending ? "Menyimpan..." : "Simpan perubahan"}
      </button>

      {update.isError ? (
        <p role="alert" className="text-sm text-alarm-coral-text">
          {update.error.message}
        </p>
      ) : null}
      {saved && !update.isPending ? (
        <p role="status" className="text-sm text-ink">
          {saved}
        </p>
      ) : null}
    </form>
  )
}
