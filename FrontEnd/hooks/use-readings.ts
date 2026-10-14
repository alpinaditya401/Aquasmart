import { skipToken, useQuery } from "@tanstack/react-query"
import { apiRequest, devicePath } from "@/lib/api/client"
import * as S from "@/lib/api/schemas"

// API.md: limit defaults to 18 and is clamped to 1-100 by the server.
export function useReadings(deviceId: string | undefined, limit = 18) {
  return useQuery({
    queryKey: ["readings", deviceId, limit] as const,
    queryFn: deviceId
      ? ({ signal }) =>
          apiRequest(devicePath(deviceId, `/readings?limit=${limit}`), S.ReadingsResponse, {
            signal,
          })
      : skipToken,
    select: (data) => data.readings,
  })
}
