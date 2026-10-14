import { fieldProps } from "@/components/ui/a11y"
import { Field } from "@/components/ui/field"
import { button, control } from "@/components/ui/styles"
import type { Device } from "@/lib/api/schemas"

const DATE_HINT = "Tanggal ini menentukan hari, minggu, atau bulan yang dihitung."

const PERIODS = [
  { value: "day", label: "Harian" },
  { value: "week", label: "Mingguan, mulai Senin" },
  { value: "month", label: "Bulanan" },
] as const

// A plain GET form: the whole filter ends up in the address bar, so a report can be
// bookmarked and reopened, and the page keeps working without client JavaScript.
export function ReportFilter({
  devices,
  value,
}: {
  devices: Pick<Device, "id" | "name">[]
  value: { device_id: string; date: string; period: string }
}) {
  return (
    <form method="get" action="/dashboard/reports" className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-3">
        <Field id="report-device" label="Perangkat">
          <select
            id="report-device"
            name="device_id"
            defaultValue={value.device_id}
            className={control()}
          >
            {devices.map((device) => (
              <option key={device.id} value={device.id}>
                {device.name}
              </option>
            ))}
          </select>
        </Field>

        <Field id="report-date" label="Tanggal (UTC)" hint={DATE_HINT}>
          <input
            name="date"
            type="date"
            defaultValue={value.date}
            className={control()}
            {...fieldProps("report-date", { hint: DATE_HINT })}
          />
        </Field>

        <Field id="report-period" label="Periode">
          <select
            id="report-period"
            name="period"
            defaultValue={value.period}
            className={control()}
          >
            {PERIODS.map((period) => (
              <option key={period.value} value={period.value}>
                {period.label}
              </option>
            ))}
          </select>
        </Field>
      </div>

      <button type="submit" className={button()}>
        Tampilkan laporan
      </button>
    </form>
  )
}
