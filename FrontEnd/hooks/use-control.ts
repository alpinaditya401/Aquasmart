import { skipToken, useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { z } from "zod"
import { apiRequest, authedRequest, devicePath } from "@/lib/api/client"
import * as S from "@/lib/api/schemas"
import { deviceKeys } from "./use-devices"

// Commands through /control are simulated (API.md: simulation=true, no GPIO, relay
// or motor). A succeeded status means the simulator acknowledged it, not that
// anything physically moved.

const commandKeys = {
  all: ["commands"] as const,
  list: (deviceId: string | undefined) => [...commandKeys.all, deviceId] as const,
  feeding: (deviceId: string | undefined) => [...commandKeys.all, deviceId, "feeding"] as const,
}

export function useCommands(deviceId: string | undefined) {
  return useQuery({
    queryKey: commandKeys.list(deviceId),
    queryFn: deviceId
      ? ({ signal }) =>
          apiRequest(devicePath(deviceId, "/commands"), S.CommandsResponse, { signal })
      : skipToken,
    select: (data) => data.commands,
  })
}

export function useFeedingLogs(deviceId: string | undefined) {
  return useQuery({
    queryKey: commandKeys.feeding(deviceId),
    queryFn: deviceId
      ? ({ signal }) =>
          apiRequest(devicePath(deviceId, "/feeding-logs"), S.FeedingLogsResponse, { signal })
      : skipToken,
    select: (data) => data.feeding_logs,
  })
}

export function useControlActuator(deviceId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: z.input<typeof S.ControlInput>) =>
      authedRequest(
        queryClient,
        devicePath(deviceId, "/control"),
        S.ControlResult,
        "POST",
        S.ControlInput.parse(input),
      ),
    // The response already carries the updated device, so patch it in place instead
    // of refetching the whole list.
    onSuccess: ({ device }) => {
      queryClient.setQueryData<z.output<typeof S.DevicesResponse>>(deviceKeys.list(), (data) =>
        data
          ? { devices: data.devices.map((known) => (known.id === device.id ? device : known)) }
          : data,
      )
      return queryClient.invalidateQueries({ queryKey: commandKeys.all })
    },
  })
}
