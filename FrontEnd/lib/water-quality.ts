import type { Thresholds } from "@/lib/api/schemas"
import { formatNumber } from "@/lib/format"

// Contract D-01 names three recorded parameters. All three are always rendered;
// a missing reading shows as "Belum ada data", never by dropping the parameter.
export type ParameterKey = "ph" | "temperature" | "turbidity"

type Parameter = {
  key: ParameterKey
  label: string
  unit: string
  decimals: number
  okLabel: string
  outLabel: string
  advice: string
}

// Labels and advice are the wording of the existing SPA (web/assets/js/app.js).
export const PARAMETERS: readonly Parameter[] = [
  {
    key: "ph",
    label: "pH Air",
    unit: "pH",
    decimals: 1,
    okLabel: "Aman",
    outLabel: "Di luar batas",
    advice: "Periksa sensor pH dan sumber air. Hindari koreksi mendadak.",
  },
  {
    key: "temperature",
    label: "Suhu Air",
    unit: "°C",
    decimals: 1,
    okLabel: "Stabil",
    outLabel: "Perlu tindakan",
    advice: "Periksa suhu dan sirkulasi air sebelum tindakan.",
  },
  {
    key: "turbidity",
    label: "Kekeruhan",
    unit: "NTU",
    decimals: 0,
    okLabel: "Dalam batas",
    outLabel: "Tinggi",
    advice: "Periksa sisa pakan, filter, dan sirkulasi air.",
  },
]

// Limits always come from the workspace thresholds returned by the server;
// ThresholdRules.php is the only place default numbers may live.
export function withinLimits(key: ParameterKey, value: number, t: Thresholds): boolean {
  if (key === "ph") return value >= t.ph_min && value <= t.ph_max
  if (key === "temperature") return value >= t.temperature_min && value <= t.temperature_max
  return value <= t.turbidity_max
}

export function limitText(key: ParameterKey, t: Thresholds): string {
  if (key === "ph") return `Batas ${formatNumber(t.ph_min, 1)} sampai ${formatNumber(t.ph_max, 1)}`
  if (key === "temperature") {
    return `Batas ${formatNumber(t.temperature_min, 1)} sampai ${formatNumber(t.temperature_max, 1)} °C`
  }
  return `Maksimum ${formatNumber(t.turbidity_max, 0)} NTU`
}
