# Sensor Event Schema

## Event Envelope

All sensor events are sent as a JSON array to `POST /api/v1/events`.

| Field        | Type   | Constraints                          | Description                        |
|--------------|--------|--------------------------------------|------------------------------------|
| `event_type` | string | `"sensor"`                           | Fixed value for sensor events      |
| `machine_id` | string | min length 1                         | Machine UUID                       |
| `user`       | string | min length 1                         | Username (typically `"system"`)    |
| `timestamp`  | string | ISO 8601 datetime                    | When the reading was taken         |
| `source`     | string | `"sensor"`                           | Source collector                   |
| `payload`    | object | required                             | Sensor-specific data (see below)   |

---

## Payload — Common Fields

Required for all sensor types.

| Field         | Type   | Values                               | Description                        |
|---------------|--------|--------------------------------------|------------------------------------|
| `sensor_id`   | string |                                      | Unique sensor identifier           |
| `sensor_type` | string | `"gyro"` \| `"sound"` \| `"magnetic"` | Sensor model type                  |
| `status`      | string | `"safe"` \| `"unsafe"`               | Reading safety classification      |
| `reason`      | string |                                      | Human-readable explanation         |

---

## Payload — MPU-6050 Gyro (`sensor_type: "gyro"`)

3-axis accelerometer + 3-axis gyroscope.

| Field | Type  | Unit  | Description             |
|-------|-------|-------|-------------------------|
| `ax`  | float | g     | Accelerometer X-axis    |
| `ay`  | float | g     | Accelerometer Y-axis    |
| `az`  | float | g     | Accelerometer Z-axis    |
| `gx`  | float | deg/s | Gyroscope X-axis        |
| `gy`  | float | deg/s | Gyroscope Y-axis        |
| `gz`  | float | deg/s | Gyroscope Z-axis        |

**Safe ranges (approximate):**

- Accelerometer: `ax` ~ 0, `ay` ~ 0, `az` ~ 9.81 (stationary upright)
- Gyroscope: all axes ~ 0 (no rotation)

**Anomaly scenarios:**

| Scenario              | Description                                                      |
|-----------------------|------------------------------------------------------------------|
| `impact_detected`     | Sudden high-g spikes — possible physical tampering or collision  |
| `freefall`            | Near-zero gravity on all axes — device in freefall or detached   |
| `sustained_vibration` | Persistent high-frequency vibration — motor fault or resonance   |
| `tilt_anomaly`        | Device tilted beyond safe operating angle — mounting shifted     |

---

## Payload — HW-485 Big Sound Sensor (`sensor_type: "sound"`)

Binary trigger sensor.

| Field       | Type | Description                      |
|-------------|------|----------------------------------|
| `triggered` | bool | `true` = loud sound detected     |

**Anomaly reasons:**

- Loud sound burst detected — possible glass break or explosion
- Sustained loud noise — possible alarm or machinery malfunction
- Repeated sound triggers in short interval — possible intrusion attempt

---

## Payload — HW-509 Magnetic Sensor (`sensor_type: "magnetic"`)

Binary trigger sensor.

| Field       | Type | Description                          |
|-------------|------|--------------------------------------|
| `triggered` | bool | `true` = magnetic field change       |

**Anomaly reasons:**

- Magnetic field change detected — door/enclosure may have been opened
- Strong magnetic interference — possible magnet-based tampering attempt
- Magnetic sensor triggered in restricted hours — unauthorized physical access

---

## Example Payloads

### Gyro — safe

```json
{
  "sensor_id": "mpu-6050-01",
  "sensor_type": "gyro",
  "ax": 0.02, "ay": -0.01, "az": 9.81,
  "gx": 0.5, "gy": -0.3, "gz": 0.1,
  "status": "safe",
  "reason": "Normal orientation and motion — readings within expected range"
}
```

### Gyro — unsafe

```json
{
  "sensor_id": "mpu-6050-01",
  "sensor_type": "gyro",
  "ax": 7.3, "ay": -5.1, "az": 3.2,
  "gx": 450.0, "gy": -280.0, "gz": 190.0,
  "status": "unsafe",
  "reason": "Sudden high-g impact detected — possible physical tampering or collision"
}
```

### Sound — triggered

```json
{
  "sensor_id": "hw485-01",
  "sensor_type": "sound",
  "triggered": true,
  "status": "unsafe",
  "reason": "Loud sound burst detected — possible glass break or explosion"
}
```

### Sound — idle

```json
{
  "sensor_id": "hw485-01",
  "sensor_type": "sound",
  "triggered": false,
  "status": "safe",
  "reason": "Ambient noise within normal threshold"
}
```

### Magnetic — triggered

```json
{
  "sensor_id": "hw509-01",
  "sensor_type": "magnetic",
  "triggered": true,
  "status": "unsafe",
  "reason": "Magnetic field change detected — door/enclosure may have been opened"
}
```

### Magnetic — idle

```json
{
  "sensor_id": "hw509-01",
  "sensor_type": "magnetic",
  "triggered": false,
  "status": "safe",
  "reason": "Magnetic field stable — enclosure sealed"
}
```

---

## Full Request Example

```bash
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '[
    {
      "event_type": "sensor",
      "machine_id": "a3f1b2c4-1234-5678-abcd-ef0123456789",
      "user": "system",
      "timestamp": "2026-04-02T10:00:00Z",
      "source": "sensor",
      "payload": {
        "sensor_id": "mpu-6050-01",
        "sensor_type": "gyro",
        "ax": 0.02, "ay": -0.01, "az": 9.81,
        "gx": 0.5, "gy": -0.3, "gz": 0.1,
        "status": "safe",
        "reason": "Normal orientation and motion — readings within expected range"
      }
    }
  ]'
```

## Response

```json
{
  "accepted": 1,
  "rejected": 0,
  "message": "Accepted 1, rejected 0"
}
```
