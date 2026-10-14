import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { z } from "zod"
import { apiRequest, authedRequest, devicePath } from "@/lib/api/client"
import * as S from "@/lib/api/schemas"

export const deviceKeys = {
  all: ["devices"] as const,
  list: () => [...deviceKeys.all, "list"] as const,
}

export function useDevices() {
  return useQuery({
    queryKey: deviceKeys.list(),
    queryFn: ({ signal }) => apiRequest("/api/devices", S.DevicesResponse, { signal }),
    select: (data) => data.devices,
  })
}

export function useClaimDevice() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: z.input<typeof S.DeviceClaimInput>) =>
      authedRequest(
        queryClient,
        "/api/devices",
        S.DeviceClaimed,
        "POST",
        S.DeviceClaimInput.parse(input),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: deviceKeys.all }),
  })
}

export function useUpdateDevice(deviceId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: z.input<typeof S.DeviceUpdateInput>) =>
      authedRequest(
        queryClient,
        devicePath(deviceId),
        S.DeviceUpdated,
        "PATCH",
        S.DeviceUpdateInput.parse(input),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: deviceKeys.all }),
  })
}

// The returned key is shown once and is never stored in any cache.
export function useRotateDeviceKey(deviceId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () =>
      authedRequest(queryClient, devicePath(deviceId, "/key"), S.DeviceKeyIssued, "POST", {}),
  })
}
