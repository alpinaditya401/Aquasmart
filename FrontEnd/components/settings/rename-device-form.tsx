"use client"

import { useRouter } from "next/navigation"
import { useId, useState } from "react"
import { fieldProps } from "@/components/ui/a11y"
import { Field } from "@/components/ui/field"
import { button, control } from "@/components/ui/styles"
import { useUpdateDevice } from "@/hooks/use-devices"
import { DeviceUpdateInput } from "@/lib/api/schemas"
import { fieldErrors } from "@/lib/form"

// One of these forms renders per device, so the label ids have to be generated.
export function RenameDeviceForm({
  deviceId,
  name,
  location,
}: {
  deviceId: string
  name: string
  location: string
}) {
  const router = useRouter()
  const update = useUpdateDevice(deviceId)
  const fieldId = useId()
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [saved, setSaved] = useState(false)

  const nameId = `${fieldId}-name`
  const locationId = `${fieldId}-location`

  function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const parsed = DeviceUpdateInput.safeParse({
      name: data.get("name"),
      location: data.get("location"),
    })
    setSaved(false)
    if (!parsed.success) {
      setErrors(fieldErrors(parsed.error))
      return
    }
    setErrors({})
    update.mutate(parsed.data, {
      onSuccess: () => {
        setSaved(true)
        router.refresh()
      },
    })
  }

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field id={nameId} label="Nama perangkat" error={errors.name}>
          <input
            name="name"
            defaultValue={name}
            maxLength={100}
            className={control()}
            {...fieldProps(nameId, { error: errors.name })}
          />
        </Field>
        <Field id={locationId} label="Lokasi" error={errors.location}>
          <input
            name="location"
            defaultValue={location}
            maxLength={150}
            className={control()}
            {...fieldProps(locationId, { error: errors.location })}
          />
        </Field>
      </div>

      <button type="submit" disabled={update.isPending} className={button({ tone: "secondary" })}>
        {update.isPending ? "Menyimpan..." : "Simpan nama dan lokasi"}
      </button>

      {update.isError ? (
        <p role="alert" className="text-sm text-alarm-coral-text">
          {update.error.message}
        </p>
      ) : null}
      {saved && !update.isPending ? (
        <p role="status" className="text-sm text-ink">
          Nama dan lokasi tersimpan.
        </p>
      ) : null}
    </form>
  )
}
