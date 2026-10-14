import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import { describe, test } from "node:test"
import type { z } from "zod"
import * as S from "./schemas.ts"

// fixtures.json holds real responses from the PHP backend: server/seed_local.php on a
// throwaway database, every browser endpoint in API.md called as admin, viewer and
// anonymous. csrf_token, device_key, invitation token and passwords are replaced by
// same-length placeholders, so the file carries no credential.

type Fixture = {
  name: string
  method: string
  path: string
  status: number
  request: unknown
  headers: Record<string, string>
  body: unknown
}

const fixtures: Fixture[] = JSON.parse(
  readFileSync(new URL("./fixtures.json", import.meta.url), "utf-8"),
)

const responseSchema: Record<string, z.ZodType> = {
  health: S.Health,
  rules: S.Rules,
  auth_login: S.Session,
  auth_me: S.Session,
  viewer_login: S.Session,
  register: S.Session,
  auth_logout: S.LoggedOut,
  profile_update: S.ProfileUpdated,
  devices_list: S.DevicesResponse,
  viewer_devices: S.DevicesResponse,
  device_claim: S.DeviceClaimed,
  device_update: S.DeviceUpdated,
  device_key_rotate: S.DeviceKeyIssued,
  readings: S.ReadingsResponse,
  readings_empty: S.ReadingsResponse,
  telemetry: S.TelemetryResponse,
  telemetry_empty: S.TelemetryResponse,
  schedules_empty: S.SchedulesResponse,
  schedules_list: S.SchedulesResponse,
  schedule_create: S.ScheduleCreated,
  schedule_delete: S.Deleted,
  control_feeder: S.ControlResult,
  control_aerator: S.ControlResult,
  control_auto: S.ControlResult,
  commands: S.CommandsResponse,
  feeding_logs: S.FeedingLogsResponse,
  alerts: S.AlertsResponse,
  alert_ack: S.AlertAcknowledged,
  alert_ack_again: S.AlertAcknowledged,
  audit_logs: S.AuditLogsResponse,
  thresholds: S.ThresholdsResponse,
  thresholds_update: S.ThresholdsResponse,
  rule_versions: S.RuleVersionsResponse,
  growth_list: S.ObservationsResponse,
  growth_create: S.ObservationCreated,
  growth_delete: S.Deleted,
  invitation_create: S.InvitationCreated,
  invitation_accept: S.InvitationAccepted,
  workspace: S.Workspace,
  workspace_member_revoke: S.MemberRevoked,
  reports_day: S.Report,
  reports_month: S.Report,
  export_json: S.ExportResponse,
  export_json_alerts: S.ExportResponse,
  export_json_commands: S.ExportResponse,
  export_json_feeding_logs: S.ExportResponse,
  export_json_reports: S.ExportResponse,
  export_json_telemetry: S.ExportResponse,
}

// Request bodies the server either accepted or rejected with 422. A client schema
// that disagrees with the server would either block valid input or let invalid
// input reach the network.
const requestSchema: Record<string, z.ZodType> = {
  auth_login: S.LoginInput,
  viewer_login: S.LoginInput,
  register: S.RegisterInput,
  device_claim: S.DeviceClaimInput,
  err_device_claim_invalid: S.DeviceClaimInput,
  device_update: S.DeviceUpdateInput,
  schedule_create: S.ScheduleInput,
  err_schedule_invalid: S.ScheduleInput,
  control_feeder: S.ControlInput,
  control_aerator: S.ControlInput,
  control_auto: S.ControlInput,
  thresholds_update: S.ThresholdsInput,
  err_thresholds_invalid: S.ThresholdsInput,
  profile_update: S.ProfileInput,
  growth_create: S.ObservationInput,
  invitation_create: S.InvitationInput,
  invitation_accept: S.InvitationAcceptInput,
}

const Provenances = [...S.Provenance.options].sort()
const isError = (f: Fixture) => f.status >= 400
const isObject = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v)

// Keys present in the captured response but absent after parsing: z.object strips
// them, so without this check an incomplete schema would pass unnoticed.
function droppedKeys(input: unknown, output: unknown, path = "$"): string[] {
  if (Array.isArray(input) && Array.isArray(output)) {
    return input.flatMap((item, i) => droppedKeys(item, output[i], `${path}[${i}]`))
  }
  if (isObject(input) && isObject(output)) {
    return Object.keys(input).flatMap((key) =>
      key in output ? droppedKeys(input[key], output[key], `${path}.${key}`) : [`${path}.${key}`],
    )
  }
  return []
}

describe("response schemas against captured responses", () => {
  test("every captured response has exactly one schema", () => {
    const names = new Set(fixtures.map((f) => f.name))
    const unmapped = fixtures
      .filter((f) => !isError(f) && !f.headers["content-type"]?.startsWith("text/csv"))
      .filter((f) => !(f.name in responseSchema))
      .map((f) => f.name)
    const stale = Object.keys(responseSchema).filter((name) => !names.has(name))
    assert.deepEqual(unmapped, [], "responses without a schema")
    assert.deepEqual(stale, [], "schemas mapped to a response that was not captured")
  })

  for (const fixture of fixtures) {
    const schema = isError(fixture) ? S.ApiErrorBody : responseSchema[fixture.name]
    if (!schema) continue
    test(`${fixture.method} ${fixture.path} (${fixture.status})`, () => {
      const result = schema.safeParse(fixture.body)
      assert.ok(result.success, result.success ? "" : JSON.stringify(result.error.issues, null, 2))
      assert.deepEqual(droppedKeys(fixture.body, result.data), [], "fields missing from the schema")
    })
  }

  test("CSV export keeps the headers the BFF has to forward", () => {
    const csv = fixtures.find((f) => f.name === "export_csv")
    assert.ok(csv, "export_csv was not captured")
    assert.match(csv.headers["content-type"] ?? "", /^text\/csv/)
    assert.match(csv.headers["content-disposition"] ?? "", /attachment; filename=/)
    assert.match(csv.headers["x-export-rows"] ?? "", /^\d+$/)
    const counts = JSON.parse(csv.headers["x-provenance-counts"] ?? "{}")
    assert.deepEqual(Object.keys(counts).sort(), Provenances)
  })
})

describe("request schemas agree with the server", () => {
  for (const [name, schema] of Object.entries(requestSchema)) {
    const fixture = fixtures.find((f) => f.name === name)
    test(`${name} is ${fixture && fixture.status === 422 ? "rejected" : "accepted"} as the server did`, () => {
      assert.ok(fixture, `${name} was not captured`)
      const result = schema.safeParse(fixture.request)
      if (fixture.status === 422) {
        assert.equal(result.success, false, "server rejected this body with 422")
      } else {
        assert.ok(fixture.status < 400, `server answered ${fixture.status}`)
        assert.ok(
          result.success,
          result.success ? "" : JSON.stringify(result.error.issues, null, 2),
        )
      }
    })
  }

  test("report and export queries match what the server accepted and rejected", () => {
    for (const fixture of fixtures.filter((f) => /^\/api\/(reports|export)\?/.test(f.path))) {
      const query = Object.fromEntries(new URL(fixture.path, "http://x").searchParams)
      const schema = fixture.path.startsWith("/api/export") ? S.ExportQuery : S.ReportQuery
      const accepted = schema.safeParse(query).success
      assert.equal(accepted, fixture.status < 400, `${fixture.path} answered ${fixture.status}`)
    }
  })

  // Rules read from ObservationRepository.php and WorkspaceRepository.php that the
  // captured fixtures do not exercise.
  test("observation dates must exist and may not lie in the future (UTC)", () => {
    const base = S.ObservationInput.parse(fixtures.find((f) => f.name === "growth_create")?.request)
    const withDate = (observed_at: string) =>
      S.ObservationInput.safeParse({ ...base, observed_at }).success
    const today = new Date().toISOString().slice(0, 10)
    const tomorrow = new Date(Date.now() + 86_400_000).toISOString().slice(0, 10)
    assert.equal(withDate(today), true)
    assert.equal(withDate(tomorrow), false)
    assert.equal(withDate("2026-02-30"), false)
    assert.equal(withDate("2026-13-01"), false)
  })

  test("invitation codes are accepted in any case and sent as issued", () => {
    const token = "AB".repeat(32)
    assert.equal(S.InvitationAcceptInput.parse({ token: ` ${token} ` }).token, "ab".repeat(32))
  })

  test("command history accepts the product unit's pump commands", () => {
    assert.equal(S.CommandActuator.safeParse("pump").success, true)
    assert.equal(
      S.ControlInput.safeParse({ actuator: "pump", value: true, request_id: "req-1" }).success,
      false,
    )
  })
})
