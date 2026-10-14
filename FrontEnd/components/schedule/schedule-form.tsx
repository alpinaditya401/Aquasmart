"use client"

import { useRouter } from "next/navigation"
import { useState } from "react"
import { fieldProps } from "@/components/ui/a11y"
import { Field } from "@/components/ui/field"
import { button, control } from "@/components/ui/styles"
import { useCreateSchedule } from "@/hooks/use-schedules"
import { ScheduleDays, ScheduleInput } from "@/lib/api/schemas"
import { fieldErrors } from "@/lib/form"

const DURATION_HINT = "1 sampai 30 detik."

export function ScheduleForm({ deviceId }: { deviceId: string }) {
  const router = useRouter()
  const create = useCreateSchedule(deviceId)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [saved, setSaved] = useState<string>()

  function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const data = new FormData(form)
    const duration = data.get("duration")
    const parsed = ScheduleInput.safeParse({
      time: data.get("time"),
      duration: duration === "" ? Number.NaN : Number(duration),
      days: data.get("days"),
    })
    if (!parsed.success) {
      setErrors(fieldErrors(parsed.error))
      return
    }
    setErrors({})
    setSaved(undefined)
    create.mutate(parsed.data, {
      onSuccess: ({ schedule }) => {
        setSaved(`Jadwal ${schedule.time} tersimpan.`)
        form.reset()
        router.refresh()
      },
    })
  }

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-3">
        <Field id="schedule-time" label="Jam (WIB)" error={errors.time}>
          <input
            name="time"
            type="time"
            required
            defaultValue="07:00"
            className={control()}
            {...fieldProps("schedule-time", { error: errors.time })}
          />
        </Field>
        <Field
          id="schedule-duration"
          label="Durasi (detik)"
          hint={DURATION_HINT}
          error={errors.duration}
        >
          <input
            name="duration"
            type="number"
            inputMode="numeric"
            min={1}
            max={30}
            defaultValue={8}
            className={control()}
            {...fieldProps("schedule-duration", { hint: DURATION_HINT, error: errors.duration })}
          />
        </Field>
        <Field id="schedule-days" label="Hari" error={errors.days}>
          <select
            name="days"
            className={control()}
            {...fieldProps("schedule-days", { error: errors.days })}
          >
            {ScheduleDays.options.map((days) => (
              <option key={days} value={days}>
                {days}
              </option>
            ))}
          </select>
        </Field>
      </div>
      <button type="submit" disabled={create.isPending} className={button()}>
        {create.isPending ? "Menyimpan..." : "Simpan jadwal"}
      </button>
      {create.isError ? (
        <p role="alert" className="text-sm text-alarm-coral-text">
          {create.error.message}
        </p>
      ) : null}
      {saved && !create.isPending ? (
        <p role="status" className="text-sm text-ink">
          {saved}
        </p>
      ) : null}
    </form>
  )
}
