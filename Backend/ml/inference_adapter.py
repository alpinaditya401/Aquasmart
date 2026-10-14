"""Adapter inferensi ML AquaSmart (V3-FR10).

Kembalikan None bila model belum tersedia. Inferensi lapangan HANYA valid
bila sensor sudah terkalibrasi — saat ini:
- turbidity: TURBIDITY_CALIBRATED=false (output raw, bukan NTU)
- TDS: belum dikalibrasi (estimasi kurva DFRobot apa adanya)
- pH: PH_STATUS=DEFERRED_NEXT_YEAR (tidak ada sensor pH air)

Aturan SKPL: prediksi TIDAK BOLEH menjadi reading, alarm terukur, atau
command otomatis. Hasil selalu membawa input window, sumber, model/version,
dan waktu target; bila data kurang/stale → status "belum tersedia".
"""
import logging
import os

log = logging.getLogger(__name__)

MODEL_PATH = os.environ.get("AQUASMART_MODEL_PATH", "")

_model = None
_model_version = None


def _load_model():
    """Muat model sekali (lazy). Return (model, version) atau (None, None)."""
    global _model, _model_version
    if _model is not None or _model_version is not None:
        return _model, _model_version
    if not MODEL_PATH or not os.path.isfile(MODEL_PATH):
        log.warning("model ML belum tersedia (AQUASMART_MODEL_PATH kosong/"
                    "tidak ada file) — predict() mengembalikan None")
        return None, None
    try:
        import joblib
        _model = joblib.load(MODEL_PATH)
        _model_version = os.path.basename(MODEL_PATH)
    except Exception as exc:  # model korup / dependensi tak cocok
        log.warning("gagal memuat model %s: %s", MODEL_PATH, exc)
        return None, None
    return _model, _model_version


def predict(features: dict) -> dict | None:
    """Prediksi status kualitas air dari fitur historis.

    Args:
        features: dict dengan kunci yang dibutuhkan model, mis.
            {"temperature": [...], "tds_mv": [...], "turbidity_mv": [...]}

    Returns:
        dict {"prediction": ..., "model": ..., "version": ...,
              "target_time": ..., "source": "ml"}
        atau None bila model belum tersedia / fitur tidak valid.
    """
    if not isinstance(features, dict) or not features:
        return None
    model, version = _load_model()
    if model is None:
        return None
    try:
        import datetime
        result = model.predict([list(features.values())])[0]
        target = (datetime.datetime.now(datetime.timezone.utc)
                  + datetime.timedelta(minutes=5)).strftime(
                      "%Y-%m-%dT%H:%M:%SZ")
        return {
            "prediction": (result.item()
                           if hasattr(result, "item") else result),
            "model": os.path.basename(MODEL_PATH),
            "version": version,
            "target_time": target,
            "source": "ml",
            "note": "prediksi informatif — bukan reading/alarm/command",
        }
    except Exception as exc:
        log.warning("inferensi gagal: %s", exc)
        return None
