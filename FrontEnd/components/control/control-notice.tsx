import { panel } from "@/components/ui/styles"
// Backend API.md: /control queues real device commands (simulation=false), and the ESP32
// takes them only when an actuator is enabled in its config. The notice sits above the
// controls, not in a footnote, because "Berhasil" in the history would otherwise read as
// proof that a motor moved.
export function ControlNotice() {
  return (
    <aside
      aria-label="Status kontrol"
      className={panel({ tone: "notice", className: "text-sm text-ink" })}
    >
      <p className="font-semibold text-sediment-text">Aktuasi fisik belum terbukti</p>
      <p className="mt-1">
        Perintah dari halaman ini disimpan server lalu diambil ESP32, tetapi hanya bila feeder atau
        relay diaktifkan di konfigurasi firmware. Bawaannya mati. Status Berhasil berarti firmware
        melaporkan keluarannya sudah diubah, bukan bukti relay atau motor bergerak.
      </p>
    </aside>
  )
}
