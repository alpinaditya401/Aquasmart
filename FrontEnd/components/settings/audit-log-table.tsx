import { TableRegion, td, th } from "@/components/ui/table-region"
import type { AuditLog } from "@/lib/api/schemas"
import { formatDateTime, provenanceLabel } from "@/lib/format"

// Wording for the actions server/src writes today. An action that is not in this map
// is printed as it comes from the server; guessing at its meaning would be worse
// than showing the raw code.
const ACTION_LABEL: Record<string, string> = {
  // Covers all three values of metadata.actuator: switching auto mode writes this
  // action without queueing any command (DeviceRepository::control).
  "actuator.control": "Aktuator atau mode otomatis diubah",
  "alert.acknowledged": "Peringatan ditandai sudah ditangani",
  "auth.login": "Masuk ke aplikasi",
  "auth.logout": "Keluar dari aplikasi",
  "auth.register": "Akun dibuat",
  "command.delivered": "Perintah diambil dari antrean",
  "command.failed": "Perintah dijawab gagal",
  "command.queued": "Perintah masuk antrean",
  "command.succeeded": "Perintah dijawab berhasil",
  "command.timeout": "Perintah tanpa balasan sampai batas waktu",
  "device.claimed": "Perangkat dihubungkan",
  "device.heartbeat": "Perangkat melapor masih hidup",
  "device.key_rotated": "Kunci perangkat diterbitkan ulang",
  "device.updated": "Nama atau lokasi perangkat diubah",
  "growth.created": "Catatan pertumbuhan ditambahkan",
  "growth.deleted": "Catatan pertumbuhan dihapus",
  "product.claimed": "Unit produk diklaim",
  "product.provisioned": "Unit produk didaftarkan",
  "profile.updated": "Profil diperbarui",
  "reading.ingested": "Pembacaan sensor masuk",
  "schedule.created": "Jadwal pakan ditambahkan",
  "schedule.deleted": "Jadwal pakan dihapus",
  "telemetry.received": "Telemetri mentah masuk",
  "thresholds.updated": "Ambang kualitas air diubah",
  "workspace.invited": "Undangan anggota dibuat",
  "workspace.joined": "Anggota bergabung",
  "workspace.revoked": "Akses anggota dicabut",
}

export function AuditLogTable({ logs }: { logs: AuditLog[] }) {
  return (
    <TableRegion label="Riwayat aktivitas, geser untuk melihat semua kolom">
      <table className="w-full min-w-[42rem] text-left text-sm">
        <thead className="bg-bg-deep text-ink">
          <tr>
            <th scope="col" className={th}>
              Waktu
            </th>
            <th scope="col" className={th}>
              Aktivitas
            </th>
            <th scope="col" className={th}>
              Perangkat
            </th>
            <th scope="col" className={th}>
              Sumber
            </th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => {
            const label = ACTION_LABEL[log.action]
            return (
              <tr key={log.id} className="border-t border-foam-line">
                <td className={`${td} text-muted`}>{formatDateTime(log.created_at)}</td>
                <td className={td}>
                  {label ?? <span className="font-data text-xs">{log.action}</span>}
                </td>
                <td className={`${td} font-data text-xs`}>
                  {log.device_id ?? (
                    <span className="font-body text-sm text-muted">Tidak terkait perangkat</span>
                  )}
                </td>
                <td className={`${td} text-xs text-muted`}>{provenanceLabel(log.provenance)}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </TableRegion>
  )
}
