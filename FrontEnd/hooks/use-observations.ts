import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { z } from "zod"
import { apiRequest, authedRequest } from "@/lib/api/client"
import * as S from "@/lib/api/schemas"

const observationKey = ["observations"] as const

export function useObservations() {
  return useQuery({
    queryKey: observationKey,
    queryFn: ({ signal }) =>
      apiRequest("/api/growth-observations", S.ObservationsResponse, { signal }),
    select: (data) => data.observations,
  })
}

export function useCreateObservation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: z.input<typeof S.ObservationInput>) =>
      authedRequest(
        queryClient,
        "/api/growth-observations",
        S.ObservationCreated,
        "POST",
        S.ObservationInput.parse(input),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: observationKey }),
  })
}

export function useDeleteObservation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (observationId: number) =>
      authedRequest(queryClient, `/api/growth-observations/${observationId}`, S.Deleted, "DELETE"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: observationKey }),
  })
}
