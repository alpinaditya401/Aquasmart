import { skipToken, useQuery } from "@tanstack/react-query"
import { apiRequest } from "@/lib/api/client"
import * as S from "@/lib/api/schemas"

// Both ReportsRepository and ExportRepository compute their windows in UTC; API.md
// adds that export weeks start on Monday.

export function useReport(query: S.ReportQuery | null) {
  return useQuery({
    queryKey: ["reports", query] as const,
    queryFn: query
      ? ({ signal }) =>
          apiRequest(`/api/reports?${new URLSearchParams(query)}`, S.Report, { signal })
      : skipToken,
  })
}

export function useExport(query: Omit<S.ExportQuery, "format"> | null) {
  return useQuery({
    queryKey: ["exports", query] as const,
    queryFn: query
      ? ({ signal }) =>
          apiRequest(
            `/api/export?${new URLSearchParams({ ...query, format: "json" })}`,
            S.ExportResponse,
            { signal },
          )
      : skipToken,
  })
}

// CSV is a download, not data for the UI. The BFF forwards Content-Disposition and
// the X-Export-Rows and X-Provenance-Counts headers unchanged.
export function exportCsvUrl(query: Omit<S.ExportQuery, "format">): `/api/export?${string}` {
  return `/api/export?${new URLSearchParams({ ...query, format: "csv" })}`
}
