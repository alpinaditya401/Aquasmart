import { panel } from "@/components/ui/styles"
// API.md: /control and the scheduler only reach the simulator. The notice sits above
// the controls, not in a footnote, because "Berhasil" in the history would otherwise
// read as proof that a motor moved.
export function SimulationNotice() {
  return (
    <aside
      aria-label="Status kontrol"
      className={panel({ tone: "notice", className: "text-sm text-ink" })}
    >
      <p className="font-semibold text-sediment-text">SIMULASI</p>
      <p className="mt-1">
        Perintah dari halaman ini dicatat server dan dijawab simulator. Tidak ada relay atau motor
        yang digerakkan, dan status Berhasil bukan bukti alat fisik bekerja.
      </p>
    </aside>
  )
}
