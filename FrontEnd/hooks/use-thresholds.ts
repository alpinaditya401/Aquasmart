import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { z } from "zod"
import { apiRequest, authedRequest } from "@/lib/api/client"
import * as S from "@/lib/api/schemas"

const thresholdKey = ["thresholds"] as const

// Thresholds are per workspace and come from the server. ThresholdRules.php is the
// only place the default numbers may be written; never hard-code them here.
export function useThresholds() {
  return useQuery({
    queryKey: thresholdKey,
    queryFn: ({ signal }) =>
      apiRequest("/api/settings/thresholds", S.ThresholdsResponse, { signal }),
    select: (data) => data.thresholds,
  })
}

export function useUpdateThresholds() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: z.input<typeof S.ThresholdsInput>) =>
      authedRequest(
        queryClient,
        "/api/settings/thresholds",
        S.ThresholdsResponse,
        "PATCH",
        S.ThresholdsInput.parse(input),
      ),
    onSuccess: (data) => queryClient.setQueryData(thresholdKey, data),
  })
}

export function useRuleVersions() {
  return useQuery({
    queryKey: ["rule-versions"] as const,
    queryFn: ({ signal }) => apiRequest("/api/rule-versions", S.RuleVersionsResponse, { signal }),
  })
}
