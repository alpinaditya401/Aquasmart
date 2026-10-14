import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { z } from "zod"
import { apiRequest, authedRequest } from "@/lib/api/client"
import * as S from "@/lib/api/schemas"

const workspaceKey = ["workspace"] as const

export function useWorkspace() {
  return useQuery({
    queryKey: workspaceKey,
    queryFn: ({ signal }) => apiRequest("/api/workspace", S.Workspace, { signal }),
  })
}

// The invitation token is returned once; keep it out of every cache.
export function useCreateInvitation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: z.input<typeof S.InvitationInput>) =>
      authedRequest(
        queryClient,
        "/api/invitations",
        S.InvitationCreated,
        "POST",
        S.InvitationInput.parse(input),
      ),
  })
}

// Accepting turns the current user into a viewer of another workspace, so the
// session and everything cached under the old role are stale.
export function useAcceptInvitation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: z.input<typeof S.InvitationAcceptInput>) =>
      authedRequest(
        queryClient,
        "/api/invitations/accept",
        S.InvitationAccepted,
        "POST",
        S.InvitationAcceptInput.parse(input),
      ),
    onSuccess: () => queryClient.invalidateQueries(),
  })
}

export function useRevokeMember() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (memberId: number) =>
      authedRequest(queryClient, `/api/workspace/members/${memberId}`, S.MemberRevoked, "DELETE"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: workspaceKey }),
  })
}
