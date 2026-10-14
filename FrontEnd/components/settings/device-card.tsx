import { RenameDeviceForm } from "@/components/settings/rename-device-form"
import { RotateKeyButton } from "@/components/settings/rotate-key-button"
import { heading, panel } from "@/components/ui/styles"
import type { Device } from "@/lib/api/schemas"
import { formatDateTime } from "@/lib/format"

export function DeviceCard({ device, isAdmin }: { device: Device; isAdmin: boolean }) {
  return (
    <article className={`${panel()} space-y-4`}>
      <div className="space-y-1">
        <h3 className={heading({ level: "sub", tone: "ink" })}>{device.name}</h3>
        <p className="text-sm text-muted">{device.location}</p>
        <p className="font-data text-xs text-muted">{device.id}</p>
      </div>

      <p className="text-sm text-ink">
        <span
          className={
            device.online ? "font-semibold text-clear-water-text" : "font-semibold text-muted"
          }
        >
          {device.online ? "Online" : "Offline"}
        </span>
        {device.last_seen
          ? `, terakhir terlihat ${formatDateTime(device.last_seen)}`
          : ", belum pernah terhubung"}
      </p>

      {isAdmin ? (
        <div className="space-y-4 border-t border-foam-line pt-4">
          <RenameDeviceForm deviceId={device.id} name={device.name} location={device.location} />
          <RotateKeyButton deviceId={device.id} deviceName={device.name} />
        </div>
      ) : null}
    </article>
  )
}
