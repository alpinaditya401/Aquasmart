import { skipToken, useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { z } from "zod"
import { apiRequest, authedRequest, devicePath } from "@/lib/api/client"
import * as S from "@/lib/api/schemas"

const scheduleKeys = {
  all: ["schedules"] as const,
  list: (deviceId: string | undefined) => [...scheduleKeys.all, deviceId] as const,
}

export function useSchedules(deviceId: string | undefined) {
  return useQuery({
    queryKey: scheduleKeys.list(deviceId),
    queryFn: deviceId
      ? ({ signal }) =>
          apiRequest(devicePath(deviceId, "/schedules"), S.SchedulesResponse, { signal })
      : skipToken,
    select: (data) => data.schedules,
  })
}

export function useCreateSchedule(deviceId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: z.input<typeof S.ScheduleInput>) =>
      authedRequest(
        queryClient,
        devicePath(deviceId, "/schedules"),
        S.ScheduleCreated,
        "POST",
        S.ScheduleInput.parse(input),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: scheduleKeys.list(deviceId) }),
  })
}

export function useDeleteSchedule(deviceId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (scheduleId: number) =>
      authedRequest(queryClient, `/api/schedules/${scheduleId}`, S.Deleted, "DELETE"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: scheduleKeys.list(deviceId) }),
  })
}
