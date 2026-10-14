import type { Device } from "@/lib/api/schemas"

// Pages share the selected device through ?device=ID so the choice survives a
// reload and can be linked. An unknown or missing id falls back to the first device.
export function pickDevice<T extends Pick<Device, "id">>(
  devices: T[],
  requested?: string,
): T | undefined {
  return devices.find((device) => device.id === requested) ?? devices[0]
}
