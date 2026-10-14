import { useQuery } from "@tanstack/react-query"
import { apiRequest } from "@/lib/api/client"
import * as S from "@/lib/api/schemas"

// API.md: limit defaults to 20 and is clamped to 1-100 by the server.
export function useAuditLogs(limit = 20) {
  return useQuery({
    queryKey: ["audit-logs", limit] as const,
    queryFn: ({ signal }) =>
      apiRequest(`/api/audit-logs?limit=${limit}`, S.AuditLogsResponse, { signal }),
    select: (data) => data.audit_logs,
  })
}
