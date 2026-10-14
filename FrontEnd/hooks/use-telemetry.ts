import { skipToken, useQuery } from "@tanstack/react-query"
import { apiRequest, devicePath } from "@/lib/api/client"
import * as S from "@/lib/api/schemas"

// Raw diagnostic telemetry. API.md: it never feeds the canonical pH or NTU values,
// and the pH input is an uncalibrated soil-sensor placeholder.
export function useTelemetry(deviceId: string | undefined) {
  return useQuery({
    queryKey: ["telemetry", deviceId] as const,
    queryFn: deviceId
      ? ({ signal }) =>
          apiRequest(devicePath(deviceId, "/telemetry"), S.TelemetryResponse, { signal })
      : skipToken,
  })
}
