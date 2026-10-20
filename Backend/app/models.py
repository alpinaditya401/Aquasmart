"""Model SQLAlchemy — dipetakan 1:1 ke skema SQLite backend PHP lama.

Tidak ada migrasi: tabel & kolom dipertahankan persis agar file
demo.sqlite / database production lama bisa dipakai langsung.
"""
from app import db

# Display labels from the PHP backend's Provenance::label(); the frontend shows
# them as the alert's source.
PROVENANCE_LABELS = {
    "simulation": "SIMULASI",
    "device": "DEVICE / kalibrasi belum diverifikasi",
    "manual": "MANUAL",
    "seed": "SEED / data contoh",
}


def provenance_label(provenance):
    return PROVENANCE_LABELS.get(provenance, "LEGACY / UNVERIFIED")


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text, unique=True, nullable=False)
    contact = db.Column(db.Text)
    password_hash = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable=False)
    role = db.Column(db.Text, nullable=False, default="admin")
    phone = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.Text, nullable=False, default=db.func.current_timestamp())
    updated_at = db.Column(db.Text, nullable=False, default=db.func.current_timestamp())
    workspace_owner_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    def safe_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "contact": self.contact,
            "name": self.name,
            "role": self.role,
            "phone": self.phone,
            # Workspace out-of-scope (Won't); frontend mewajibkan field ini
            # (nullable) sesuai kontrak backend PHP lama.
            "workspace_owner_id": None,
        }


class Device(db.Model):
    __tablename__ = "devices"
    id = db.Column(db.Text, primary_key=True)  # serial, mis. AQS-KOLAM-01
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.Text, nullable=False)
    location = db.Column(db.Text, nullable=False)
    online = db.Column(db.Integer, nullable=False, default=0)
    aerator = db.Column(db.Integer, nullable=False, default=0)
    feeder = db.Column(db.Integer, nullable=False, default=0)
    auto_mode = db.Column(db.Integer, nullable=False, default=0)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    last_seen = db.Column(db.Text)
    created_at = db.Column(db.Text, nullable=False, default=db.func.current_timestamp())
    updated_at = db.Column(db.Text, nullable=False, default=db.func.current_timestamp())


class DeviceCredential(db.Model):
    __tablename__ = "device_credentials"
    device_id = db.Column(db.Text, db.ForeignKey("devices.id"), primary_key=True)
    key_hash = db.Column(db.Text, nullable=False)  # SHA-256 hex dari X-Device-Key
    rotated_at = db.Column(db.Text, nullable=False)


class DeviceTelemetry(db.Model):
    __tablename__ = "device_telemetry"
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Text, db.ForeignKey("devices.id"), nullable=False)
    created_at = db.Column(db.Text, nullable=False)
    received_at = db.Column(db.Text, nullable=False)
    provenance = db.Column(db.Text, nullable=False)  # device | simulation
    simulation = db.Column(db.Integer, nullable=False)
    source_session = db.Column(db.Text, nullable=False)
    payload = db.Column(db.Text, nullable=False)  # JSON mentah
    # Sumber data eksplisit: 'simulated' | 'hardware' (ditambah V4.0;
    # backfill 'simulated' untuk data lama). Berbeda dari provenance yang
    # merupakan kontrak firmware frozen.
    source = db.Column(db.Text)
    __table_args__ = (db.UniqueConstraint("device_id", "created_at"),)


class SensorReading(db.Model):
    __tablename__ = "sensor_readings"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.Text, db.ForeignKey("devices.id"), nullable=False)
    ph = db.Column(db.Float, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    turbidity = db.Column(db.Float, nullable=False)
    simulation = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.Text, nullable=False)
    provenance = db.Column(db.Text, nullable=False, default="legacy_unverified")
    source_session = db.Column(db.Text)
    __table_args__ = (db.UniqueConstraint("device_id", "created_at"),)


class ActuatorCommand(db.Model):
    __tablename__ = "actuator_commands"
    id = db.Column(db.Text, primary_key=True)  # hex 32
    device_id = db.Column(db.Text, db.ForeignKey("devices.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    actuator = db.Column(db.Text, nullable=False)
    value = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    request_id = db.Column(db.Text, nullable=False)
    status = db.Column(db.Text, nullable=False, default="pending")
    simulation = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.Integer, nullable=False)  # unix ts
    expires_at = db.Column(db.Integer, nullable=False)
    delivered_at = db.Column(db.Integer)
    completed_at = db.Column(db.Integer)
    provenance = db.Column(db.Text, nullable=False, default="legacy_unverified")
    source_session = db.Column(db.Text)
    __table_args__ = (db.UniqueConstraint("device_id", "request_id"),)

    TERMINAL = ("succeeded", "failed", "timeout")

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "actuator": self.actuator,
            "value": bool(self.value),
            "duration": self.duration,
            "request_id": self.request_id,
            "status": self.status,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }


class ThresholdSetting(db.Model):
    __tablename__ = "threshold_settings"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    ph_min = db.Column(db.Float, nullable=False, default=6.5)
    ph_max = db.Column(db.Float, nullable=False, default=8.5)
    temperature_min = db.Column(db.Float, nullable=False, default=25.0)
    temperature_max = db.Column(db.Float, nullable=False, default=30.0)
    turbidity_max = db.Column(db.Float, nullable=False, default=50.0)


class RuleVersion(db.Model):
    __tablename__ = "rule_versions"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    version = db.Column(db.Text, nullable=False)
    config_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.Text, nullable=False, default=db.func.current_timestamp())


class Alert(db.Model):
    __tablename__ = "alerts"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.Text, db.ForeignKey("devices.id"))
    severity = db.Column(db.Text, nullable=False)
    message = db.Column(db.Text, nullable=False)
    acknowledged = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.Text, nullable=False, default=db.func.current_timestamp())
    acknowledged_at = db.Column(db.Text)
    acknowledged_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    provenance = db.Column(db.Text, nullable=False, default="legacy_unverified")
    source_session = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "severity": self.severity,
            "message": self.message,
            "source": provenance_label(self.provenance),
            "acknowledged": bool(self.acknowledged),
            "created_at": self.created_at,
            "acknowledged_at": self.acknowledged_at,
            "acknowledged_by": self.acknowledged_by,
            "provenance": self.provenance,
            "source_session": self.source_session,
        }


class FeedingSchedule(db.Model):
    __tablename__ = "feeding_schedules"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.Text, db.ForeignKey("devices.id"), nullable=False)
    time = db.Column(db.Text, nullable=False)  # HH:MM
    duration = db.Column(db.Integer, nullable=False)  # menit, 1-30
    days = db.Column(db.Text, nullable=False)
    active = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.Text, nullable=False,
                           default=db.func.current_timestamp())
    updated_at = db.Column(db.Text, nullable=False,
                           default=db.func.current_timestamp())

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "time": self.time,
            "duration": self.duration,
            "days": self.days,
            "active": bool(self.active),
            "created_at": self.created_at,
        }


class GrowthObservation(db.Model):
    __tablename__ = "growth_observations"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    device_id = db.Column(db.Text, db.ForeignKey("devices.id"), nullable=False)
    observed_at = db.Column(db.Text, nullable=False)
    weight_g = db.Column(db.Float)
    length_cm = db.Column(db.Float)
    notes = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.Text, nullable=False,
                           default=db.func.current_timestamp())
    provenance = db.Column(db.Text, nullable=False, default="legacy_unverified")
    source_session = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "device_id": self.device_id,
            "observed_at": self.observed_at,
            "weight_g": self.weight_g,
            "length_cm": self.length_cm,
            "notes": self.notes,
            "created_at": self.created_at,
            "provenance": self.provenance,
            "source_session": self.source_session,
        }


class DeviceInventory(db.Model):
    __tablename__ = "device_inventory"
    serial_number = db.Column(db.Text, primary_key=True)
    default_name = db.Column(db.Text, nullable=False)
    default_location = db.Column(db.Text, nullable=False)
    claimed_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    claimed_at = db.Column(db.Text)
    created_at = db.Column(db.Text, nullable=False,
                           default=db.func.current_timestamp())
