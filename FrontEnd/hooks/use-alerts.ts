import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { apiRequest, authedRequest } from "@/lib/api/client"
import * as S from "@/lib/api/schemas"

const alertKeys = {
  all: ["alerts"] as const,
  list: (limit: number) => [...alertKeys.all, limit] as const,
}

// API.md: limit defaults to 20 and is clamped to 1-100 by the server.
export function useAlerts(limit = 20) {
  return useQuery({
    queryKey: alertKeys.list(limit),
    queryFn: ({ signal }) => apiRequest(`/api/alerts?limit=${limit}`, S.AlertsResponse, { signal }),
  })
}

// Acknowledging is idempotent on the server, so a double click is harmless.
export function useAcknowledgeAlert() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (alertId: number) =>
      authedRequest(
        queryClient,
        `/api/alerts/${alertId}/acknowledge`,
        S.AlertAcknowledged,
        "PATCH",
        {},
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: alertKeys.all }),
  })
}
