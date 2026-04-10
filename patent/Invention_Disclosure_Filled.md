# INVENTIVE DISCLOSURE – CONFIDENTIAL

**Prepared in the format of:** Khurana & Khurana Invention Disclosure Form
**Date:** 11 April 2026

---

## 1. Title of the Invention

**A Privacy-Preserving, Cross-Layer Threat Detection and Insider-Risk Platform for Critical Healthcare Infrastructure Using Edge Sensor Fusion, Hashed Behavioral Monitoring, Isolation-Forest-Based Anomaly Detection, and Explainable Risk Scoring.**

(Working name: *MedGuard Threat Engine*.)

---

## 2. Technical Field of Invention

The invention lies in the technical field of **cybersecurity for medical and healthcare infrastructure**, specifically at the intersection of **IoT physical-integrity monitoring**, **host-based behavioral analytics**, **privacy-preserving data processing (Private Set Intersection, PSI)**, and **explainable machine learning (XAI)** for anomaly detection.

**Problem statement.** Hospitals, clinics, research labs, and pharmacies operate a heterogeneous fleet of life-critical and regulation-bound equipment — ventilators, infusion pumps, patient monitors, vaccine and blood refrigerators, narcotics and drug cabinets, portable diagnostic devices, and restricted lab instruments. These devices face two simultaneous and largely uncorrelated classes of threats: (i) **physical tampering, theft, misplacement, and environmental faults**, and (ii) **digital misuse** such as unauthorized logins, malicious shell commands, privilege escalation, or insider policy violations by staff. Existing security products treat these two threat classes in silos: IT endpoint-detection tools ignore the physical world, and hospital physical-security tools (CCTV, door sensors) ignore the host behavior. Furthermore, shipping raw command lines and raw patient-adjacent data off the device is unacceptable under HIPAA, GDPR, and DPDP-style regimes.

**Solution statement.** The invention provides a single **cross-layer threat engine** that fuses (a) physical sensor events from MEMS/IoT sensors attached to medical equipment with (b) host-level behavioral events from a lightweight Linux endpoint agent that **never transmits raw commands** — only SHA-256 hashes normalized per a shared scheme. The engine uses (i) **Private Set Intersection (PSI)** against a hashed threat command database, (ii) an **unsupervised Isolation Forest** anomaly model trained on fused physical + digital feature vectors with device-criticality weighting, and (iii) an **Explainable AI (XAI) layer** that produces human-readable, clinician-friendly justifications. It additionally learns per-role baselines for healthcare staff (nurses, technicians, pharmacists, admins) to detect **insider-risk operational sequences** without profiling identity or intent.

**General purpose.** To protect patient safety and regulated assets by detecting, correlating, scoring, and explaining threats that span the physical and digital layers of a healthcare environment, in real time, while preserving privacy of both patients and staff.

---

## 3. Search Terms

Medical device cybersecurity; hospital IoT security; privacy-preserving intrusion detection; private set intersection command hashing; Isolation Forest anomaly detection; explainable AI security; healthcare insider threat detection; MPU-6050 tamper detection; vibration-based tamper detection; infusion pump security; ventilator cybersecurity; HIPAA-compliant EDR; sensor fusion anomaly detection; cross-layer threat correlation; temporal threat chaining; behavioral baselining for clinicians; shift-aware access control; vaccine refrigerator monitoring; narcotics cabinet tamper detection; SHA-256 command normalization.

---

## 4. Background of the Invention (Present State of Art)

**Present technologies in the field.**

1. **Traditional Endpoint Detection and Response (EDR) / Host IDS** (e.g., generic SIEM agents, auditd-based tools). These monitor authentication, processes, and commands on Linux/Windows hosts and forward raw logs to a central server.
2. **Medical device management platforms** (asset inventory / firmware version tracking) that enumerate connected devices on hospital networks and flag outdated firmware or unpatched CVEs.
3. **Physical security systems** — CCTV, RFID badges, magnetic door contacts, and BMS-integrated intrusion alarms — which monitor rooms, cabinets, and enclosures independently of any host software.
4. **Isolated IoT tamper sensors** (accelerometer-based or reed-switch-based) that raise a hardware alarm but do not integrate with host behavior.
5. **Rule-based insider-threat tools** using static access-control lists and fixed hour windows.

**Limitations of the present art.**

- **Silos.** Physical and digital telemetry are analyzed separately; an attacker who opens a drug cabinet AND runs a suspicious configuration command on the paired workstation triggers at most two unlinked low-severity alerts, never a single high-severity correlated chain.
- **Privacy exposure.** Conventional EDR ships raw command lines and raw filesystem paths off the endpoint; this is at odds with HIPAA/GDPR/DPDP for devices that live next to patient data.
- **No device-criticality context.** A generic EDR treats a compromise of a coffee-room PC and of an ICU ventilator controller identically.
- **Static rules for insiders.** Fixed ACLs do not model that "Nurse A normally uses Infusion Pump #12 during the 07:00–19:00 shift" — they cannot detect a legitimate credential used in an illegitimate *pattern*.
- **Opaque ML.** Where ML is used at all, it is typically a black box; clinical staff and hospital administrators cannot act on an unexplained risk score.
- **No predictive / pre-tamper detection.** Existing tools react after the breach; they do not use sensor drift to predict imminent tampering or device failure.

---

## 5. Prior Art

The following representative prior technologies have been considered:

1. **Generic Linux EDR / auditd-based host monitoring.** Collects auth logs, shell history, and process execution. Ships raw data. No physical-world input. No PSI. No healthcare context.
2. **Accelerometer-based tamper-evident enclosures** (e.g., ATM and POS tamper sensors using MEMS accelerometers such as the MPU-6050 family). Trigger a local alarm on impact or tilt. No fusion with host behavior.
3. **Hospital asset-tracking platforms** (RFID/BLE-based). Track *location* of medical equipment but not its *operational security state*.
4. **Isolation Forest anomaly detection** as published by Liu, Ting, and Zhou (2008) — a general unsupervised anomaly algorithm. Prior uses include network-flow anomaly detection and credit-card fraud; healthcare physical+digital sensor fusion use has not been demonstrated in prior art to the inventors' knowledge.
5. **Private Set Intersection (PSI) literature** for privacy-preserving set membership. Used historically in contact discovery and ad measurement; not previously deployed as the primary command-safety check of a medical EDR.
6. **UEBA (User and Entity Behavior Analytics) products.** Build baselines of user behavior but rely on raw log content and are not designed around hashed command fingerprints or physical sensor signals.
7. **Published research on vibration / acoustic tamper detection** for safes and cabinets — hardware-only pipelines, no correlation with host-layer events.

No single prior work has been identified that combines: hashed-command PSI **plus** fused MEMS + acoustic + magnetic sensor feature vectors **plus** Isolation-Forest anomaly detection **plus** XAI output **plus** healthcare-role-aware insider baselining, under a single temporal correlation engine specifically for medical infrastructure.

---

## 6. Has the Work Filled a Major Gap in the Prior Art?

**Yes.** The gap filled is the absence of a **cross-layer, privacy-preserving, explainable threat detection platform purpose-built for healthcare**. Prior art forces hospitals to buy an EDR (digital), a physical intrusion system (physical), and an asset tracker (inventory) from three different vendors, none of which talk to each other, none of which are hash-only, and none of which weight alerts by whether the affected device is a bedside ventilator or a lobby printer. This invention collapses those three silos into a single engine whose core novelty is the **temporal fusion of a command hash with a physical sensor event on the same device, scored by a single unsupervised model, and explained in a single natural-language sentence a nurse or administrator can act on**.

---

## 7. Components of the Invention

The invention comprises four cooperating subsystems plus a shared data contract.

### 7.1 Endpoint Agent (`agent/`)
A lightweight Linux service installed on medical workstations, bedside controllers, and Linux-based embedded medical devices.
- **AuthCollector** — reads `/var/log/auth.log` or `journalctl` for login/logout/sudo/failed-auth events.
- **CommandCollector** — reads shell history (e.g., `/home/*/.bash_history`), applies the shared normalization (trim → collapse whitespace → lowercase) and computes **SHA-256** per command. **Only `command_hash` and `command_length` leave the device. Raw command text never leaves the device.**
- **ProcessCollector** — samples running processes (exe, argv, pid, parent_pid, start_time).
- **Buffer** — in-memory buffer with optional on-disk persistence (`AGENT_PERSIST_PATH`) so that events survive a reboot of a ward workstation.
- **Sender** — HTTPS POST to the engine with `Authorization: Bearer <AGENT_API_KEY>`, exponential backoff, and batching.

### 7.2 Hardware Sensor Layer
Physical sensors mounted on or inside the monitored equipment and its enclosure.
- **MPU-6050** — 3-axis accelerometer (g) + 3-axis gyroscope (°/s). Detects impact, free-fall (device detached/dropped), sustained vibration (motor fault, pump cavitation, drill attack), and tilt deviation (enclosure moved).
- **HW-485 Big Sound Sensor** — binary acoustic trigger for loud burst, sustained loud noise, or repeated triggers (possible glass break, cabinet forced open, or alarm loop).
- **HW-509 Magnetic Sensor** — binary magnetic trigger on enclosures, drug-cabinet doors, and access panels; also detects strong external magnets used to defeat conventional reed-switch sensors.

Each sensor is paired with a low-cost edge MCU (e.g., ESP32 / RP2040) that POSTs directly to the engine as `event_type = "sensor"`, carrying `sensor_type`, `sensor_id`, and a `device_criticality` tag (e.g., `icu_ventilator`, `vaccine_fridge`, `narcotics_cabinet`, `general_ward`).

### 7.3 Detection Engine (`engine/`) — the core inventive subsystem
A FastAPI service backed by PostgreSQL that runs the four-stage pipeline:

1. **Ingest & Validate** against the shared JSON event schema.
2. **PSI Check.** For `command` events, look up `command_hash` against an in-memory + DB-backed set of known malicious hashes (`engine/psi/checker.py`). Hit → immediate high-risk flag + category.
3. **Feature Extraction.**
   - Host features: hour-of-day, day-of-week, user bucket, machine bucket, source encoding, command-hash bucket, event-type one-hot.
   - Sensor features: `ax, ay, az` clipped to ±1 at ±16 g; `gx, gy, gz` clipped to ±1 at ±2000 °/s; `triggered ∈ {0.0, 1.0}`; `sensor_type` encoding; `device_criticality` weight.
   - **Cross-layer features** (the inventive part): within a sliding temporal window per `machine_id`, the engine injects co-occurrence indicators such as `phys_event_within_60s`, `magnetic_open_then_login`, `vibration_during_cmd`, and `sensor_then_process_spawn`.
4. **Isolation Forest Scoring.** A global `IsolationForest` (with per-device-class sub-models) maps the fused feature vector to an anomaly score, renormalized to **risk ∈ [0, 100]**. Device criticality scales the final risk.
5. **XAI Explanation.** `engine/xai/explainer.py` generates a short natural-language justification containing: the dominant contributing features, whether a PSI hit occurred, the temporal chain that was fused (e.g., *"magnetic door opened 12 s before shell login; then `command_hash=…` scored high-anomaly"*), and a clinician-readable severity label.
6. **Persistence** in `raw_event`, `processed_event`, and `alert` tables. An alert is raised iff `risk ≥ ENGINE_ALERT_THRESHOLD` (default 50).

### 7.4 Insider-Risk Baselining Module
Per-role, per-shift baselines learned unsupervised for nurses, technicians, pharmacists, and admins: typical machines, typical hours, typical command-hash distribution, typical sensor-interaction patterns. Deviations (e.g., pharmacist touching an ICU ventilator at 03:00, or a tech generating narcotics-cabinet magnetic events outside their assigned ward) feed additional features into the same Isolation Forest so that insider signals and outsider signals share one scoring surface.

### 7.5 Web Dashboard (`dashboard/`)
React + TypeScript + Vite. Pages: **Dashboard** (overview), **Alerts** (list + detail + XAI block), **Activity** (timeline of processed events with risk badges), **Sensors** (live gyro/accel charts, trigger history, per-device risk). Auto-refresh for live wards.

### 7.6 Shared Contract (`shared/event_schema.json`)
A single JSON schema for all event types (`auth`, `command`, `process`, `sensor`), enforcing that `command` events carry only `command_hash` + metadata — **never** raw command text — so privacy is guaranteed by schema, not by policy.

---

## 8. How Does the Invention Work?

**Step-by-step operational flow:**

1. **Deployment.** The agent is installed on every Linux-capable medical workstation. Sensors are mounted to the monitored equipment: MPU-6050 screwed to the ventilator chassis, HW-509 on the narcotics cabinet door, HW-485 in the vaccine-fridge room.
2. **Event generation.** The agent tails `auth.log`, user shell histories, and the process table. For each shell command it normalizes (`strip → collapse whitespace → lowercase`) and hashes (`SHA-256`) before it ever leaves RAM. Sensors push raw physical readings over HTTPS to the engine.
3. **Ingestion.** All events land at `POST /api/v1/events` and are persisted as `RawEvent`s.
4. **PSI gate.** For `command` events the engine asks: *is `command_hash ∈ threat_hashes`?* Because this is a set-membership test over hashes, the engine learns nothing about the command except "malicious yes/no" plus category.
5. **Cross-layer temporal fusion.** The engine maintains a short per-`machine_id` sliding window (configurable, default 120 s) of recent events across all layers. When a new event arrives, fusion features are computed: e.g., `magnetic_trigger_in_last_30s`, `vibration_energy_last_10s`, `failed_auths_last_5m`, `sensor_then_cmd`, `cmd_then_sensor`.
6. **Isolation Forest scoring.** The fused feature vector is scored against the global model (persisted as `data/models/global_model.joblib`). The raw anomaly score is renormalized to 0–100 and multiplied by a device-criticality factor (e.g., ×1.0 for `general_ward`, ×1.5 for `vaccine_fridge`, ×2.0 for `icu_ventilator`, ×2.2 for `narcotics_cabinet`).
7. **XAI explanation.** The explainer inspects the contributing factors — which features pushed the score up, whether PSI fired, whether a physical–digital chain was detected — and emits a single paragraph such as:
   > *"Risk 87/100. Narcotics cabinet (HW-509) was opened at 02:14:03. Within 17 seconds a shell session on workstation NURSE-03 executed a command whose hash matches known sudoers-tamper activity. User ‘tech_09’ is not scheduled on this ward during night shift. Recommended action: lock session and page pharmacy lead."*
8. **Alerting.** If `risk ≥ threshold`, a row is written to `alerts`; the dashboard's auto-refreshing Alerts page shows the card with the XAI block and a one-click drill-down to the fused event chain.
9. **Continuous learning.** The Isolation Forest is periodically re-fit from the accumulating `processed_events` table so baselines drift with the hospital's real operational rhythm (shift changes, new devices, seasonal staffing).
10. **Predictive mode.** Sensor trend features (e.g., slow drift in vibration RMS on an infusion pump, gradual tilt change on a monitor mount) feed the same model so that *pre-tamper* and *pre-failure* states are surfaced before an incident occurs.

---

## 9. Novelty / Inventive Step

The unique and non-obvious aspects of this invention are:

1. **Cross-layer temporal fusion as a first-class feature.** Existing systems concatenate physical and digital alerts at a UI level at best. This invention fuses them at the **feature-vector level** before anomaly scoring, so the Isolation Forest learns the *joint* distribution and can flag a chain that is benign in either layer alone.
2. **Hash-only command telemetry via PSI.** The shared normalization + SHA-256 + PSI-style set-membership check means the server never sees a raw command, yet can still detect known-malicious behavior. This is structurally privacy-preserving — the privacy property is enforced by the schema and the hash function, not by a data-handling policy.
3. **Device-criticality-weighted risk.** The same anomaly is scored differently on an ICU ventilator than on a lobby kiosk. This criticality weighting is baked into the ML output, not bolted on as a post-hoc rule.
4. **Explainable output for a non-ML audience.** Every alert carries an XAI paragraph written for clinicians and hospital administrators, citing both the physical and the digital contributors.
5. **Role- and shift-aware insider baselining** using unsupervised features (not static ACLs), so that legitimate credentials used in illegitimate patterns are caught without profiling identity or intent.
6. **Single engine, single model surface** for outsider attacks, insider misuse, physical tampering, and device-health precursors — these are traditionally four different products.

---

## 10. Advantages and Improvements over Existing Methods

- **Privacy by construction:** HIPAA/GDPR/DPDP-friendly because raw commands and raw patient-context data never leave the endpoint.
- **Fewer silos, fewer vendors:** replaces separate EDR + physical-intrusion + asset-tracking tools with one dashboard.
- **Lower false-positive rate:** cross-layer fusion suppresses alerts that look anomalous in one layer but are benign in context (e.g., a loud sound burst during a scheduled maintenance window whose workstation shows a normal technician login).
- **Higher true-positive rate on subtle attacks:** catches multi-step attacks — physical access → digital misuse — that neither a pure EDR nor a pure door sensor would catch.
- **Criticality-aware triage:** hospital security staff see the ICU ventilator alert above the lobby-printer alert automatically.
- **Explainability:** reduces mean time to action because the nurse-in-charge does not need a data scientist to interpret the score.
- **Predictive maintenance side-benefit:** the same sensor pipeline identifies early mechanical faults, so the platform delivers both safety and uptime value.
- **Low cost:** uses commodity sensors (MPU-6050, HW-485, HW-509) and commodity MCUs; software stack is open-source (FastAPI, PostgreSQL, scikit-learn, React).

---

## 11. Alternative Embodiments / Variants

1. **Federated learning variant.** Instead of a single global Isolation Forest, each hospital trains a local model and only model parameters (not events) are aggregated across hospitals, improving detection of rare attack patterns without sharing events.
2. **Homomorphic PSI variant.** Replace plain SHA-256 + set lookup with an OPRF-based PSI protocol so that the engine cannot even enumerate the threat set during comparison.
3. **Wearable-integrated embodiment.** Staff wear BLE badges that feed presence into the fusion window; "command executed on Pump #3 with no authorized badge in the room" becomes a fusion feature.
4. **Veterinary and pharma-manufacturing embodiments.** Same engine, different criticality weights for vaccine cold chain, GMP clean rooms, and animal-care equipment.
5. **Drone and ambulance embodiment.** Sensors and agent on mobile medical units; GPS becomes an extra fusion feature for geofenced drug transport.
6. **On-device inference embodiment.** Push the Isolation Forest to the MCU/edge so that alerts can fire even during a network outage.
7. **Replacement of Isolation Forest** with an autoencoder or LOF as drop-in anomaly scorers while keeping the fusion/PSI/XAI scaffolding.
8. **Pluggable sensor set.** Add temperature (for cold chain), humidity, CO₂, or current-clamp sensors for device-power fingerprinting.

---

## 12. CAD Images / Line Diagrams

*(To be supplied by the inventors. Recommended figures, each in labeled and unlabeled versions:)*

- **Fig. 1** — System block diagram: Endpoint Agent, Sensor Layer, Detection Engine (with PSI / Feature Extraction / Isolation Forest / XAI sub-blocks), PostgreSQL, Dashboard.
- **Fig. 2** — Cross-layer temporal fusion window, showing how a magnetic-open event, a sound-burst event, and a command-hash event within 120 s collapse into a single feature vector.
- **Fig. 3** — Mechanical mounting of MPU-6050, HW-485, HW-509 on a representative medical device (e.g., narcotics cabinet and infusion pump).
- **Fig. 4** — Data-flow / pipeline flowchart: `Ingest → PSI → Feature Extraction → Isolation Forest → XAI → Alert/Store`.
- **Fig. 5** — Dashboard screenshots: Alerts page with XAI block, Sensors live-chart page.
- **Fig. 6** — Insider-risk baselining schematic: per-role, per-shift envelope vs. observed behavior.

---

## 13. Brief Inventor Description of the Drawings

Fig. 1 shows the three physical layers of the system and how all telemetry converges on the FastAPI Detection Engine, which is the inventive heart. Fig. 2 illustrates the key inventive step — the sliding temporal window that turns separate physical and digital events into one joint feature vector. Fig. 3 shows how the off-the-shelf sensors are non-invasively mounted on regulated medical hardware without voiding device certification. Fig. 4 is the end-to-end runtime pipeline; note that the PSI stage short-circuits known-bad commands before ML, while ML handles the unknown-unknown space. Fig. 5 demonstrates that the final output seen by a clinician or hospital administrator is a single sentence they can act on, not a raw score. Fig. 6 shows how the insider-risk module envelopes a legitimate clinician's normal behavior and flags out-of-envelope sequences.

---

## 14. Complete Description / Working Example

**Working example: Narcotics cabinet tamper with insider credentials.**

*Setup.* A narcotics cabinet in Ward-B is fitted with an HW-509 magnetic sensor and an HW-485 sound sensor. The paired workstation `WS-WARDB-03` runs the endpoint agent. Device criticality = `narcotics_cabinet` (weight ×2.2). `ENGINE_ALERT_THRESHOLD = 50`.

*Timeline (all within 45 seconds).*

| t (s) | Layer | Event | Raw meaning |
|------:|-------|-------|-------------|
| 0 | Sensor | `sensor / magnetic / triggered=true` | Cabinet door opened |
| 3 | Sensor | `sensor / sound / triggered=true` | Loud clink |
| 8 | Host | `auth / login success` user `tech_09` | Shell login |
| 11 | Host | `command / command_hash=0x9f…` | (hash of a privilege-changing command) |
| 14 | Host | `process / exe=/usr/bin/sqlite3, argv=medlog.db` | DB touched |

*Engine behavior.*

1. All five events are persisted as `RawEvent` and enter the 120 s fusion window for `machine_id = WS-WARDB-03`.
2. PSI check on the command hash at t=11 returns **hit**, category `sudoers_tamper`. Base risk is already elevated.
3. Feature extraction builds a single vector including `magnetic_open_in_last_30s=1`, `sound_trigger_in_last_30s=1`, `failed_auths_last_5m=0`, `cmd_after_physical=1`, `hour=02`, `user_role=tech`, `user_on_shift=0`, `device_criticality=narcotics_cabinet`.
4. Isolation Forest scores the vector as strongly anomalous; normalized risk = 41; criticality weight ×2.2 → **risk = 90**.
5. XAI explainer emits:
   > *"Critical: narcotics cabinet opened at 02:14:03, loud acoustic event 3 s later, followed 8 s later by an off-shift login from ‘tech_09’ (not rostered to Ward-B tonight) and a shell command matching a known sudoers-tamper fingerprint. Recommended: revoke session, page pharmacy lead, preserve logs."*
6. An `Alert` row is written with `risk=90`, `kind=cross_layer_insider_narcotics`, XAI text attached, and surfaced on the dashboard within one auto-refresh tick.

A **pure EDR** would only have seen a suspicious command from a legitimate user — low severity. A **pure physical alarm** would only have seen a cabinet opening — routine during shift hours. Only the fused engine produces the correct high-severity, explainable, actionable alert.

---

## 15. Experiments / Third-Party Validation

*(Placeholder for the inventors to fill with real measurements.)*

Planned / preliminary evaluation:

- **Dataset.** Synthetic + simulated using `scripts/sensor_simulator.py` and `scripts/demo_agents.py`, injecting ~15% anomalous gyro/sound events and ~10% anomalous magnetic events, plus PSI-hit command traffic.
- **Metrics.** Precision, recall, F1, and time-to-alert for (a) host-only baseline, (b) sensor-only baseline, (c) fused cross-layer engine. Expected improvement from fusion: **+18–25 % F1** and **~3× reduction in false-positive rate** relative to the better of the two single-layer baselines.
- **Planned third-party validation.** Hospital IT + biomedical engineering department pilots; independent red-team tamper exercises on a decommissioned narcotics cabinet and a test ventilator rig.

---

## 16. Public Disclosure / Publications

No public disclosure, publication, conference talk, or open-source release of the inventive cross-layer fusion + PSI + XAI combination has been made as of the date of this form. The underlying open-source building blocks (FastAPI, scikit-learn Isolation Forest, React) are public, but their specific composition and the inventive fusion logic have not been disclosed.

---

## 17. Stage / Level of Development

**Between TRL 4 and TRL 5.** The base platform (endpoint agent, engine, PSI checker, Isolation Forest scorer, XAI explainer, dashboard, three sensor types, Docker stack, migrations, tests) is implemented and working end-to-end in a lab environment with simulated events. The healthcare-specific extensions — device-criticality weighting, cross-layer fusion features, role/shift insider baselining, and the medical-fleet schema — are partially implemented and validated on synthetic data. Clinical pilot deployment has not yet begun.

- [ ] (a) Basic conceptualization stage
- [x] (b) Implemented and results validated in a lab/simulated environment; clinical validation pending.

---

## 18. Proposed Claims (Aspects to Monopolize)

1. **A healthcare threat-detection system** comprising a Linux endpoint agent that transmits shell commands only as normalized SHA-256 hashes, a set of physical sensors mounted on medical equipment (at minimum a MEMS inertial sensor, an acoustic sensor, and a magnetic sensor), and a detection engine that ingests both streams under a unified event schema.
2. **The system of claim 1**, wherein the engine maintains a per-device temporal fusion window and computes joint feature vectors combining host-behavioral features and physical sensor features before scoring.
3. **The system of claim 2**, wherein the joint feature vectors are scored by an unsupervised Isolation Forest whose output is renormalized to a 0–100 risk and multiplied by a device-criticality weight reflecting the clinical impact of the monitored equipment.
4. **The system of claim 1**, wherein command events are checked for maliciousness via a Private Set Intersection-style set-membership test over SHA-256 hashes such that the engine never observes raw command text.
5. **The system of any preceding claim**, wherein an explainable-AI module generates a natural-language justification citing both the physical and the digital contributing factors of each alert.
6. **The system of any preceding claim**, further comprising a role- and shift-aware insider-risk module that learns unsupervised baselines per staff role and flags deviations as additional features to the same anomaly model, without profiling personal identity or intent.
7. **The system of any preceding claim**, wherein sensor trend features are additionally used to produce pre-tamper and pre-failure predictions for medical equipment.
8. **A method** of detecting cross-layer threats in a healthcare environment, comprising the steps of: (i) collecting hashed behavioral events from a host, (ii) collecting physical sensor events from the same device, (iii) fusing both within a temporal window into a single feature vector, (iv) scoring with an Isolation Forest weighted by device criticality, and (v) producing a human-readable explanation.
9. **A non-transitory computer-readable medium** storing instructions that, when executed, perform the method of claim 8.
10. **The system of claim 1**, in a federated embodiment in which multiple hospitals share only model parameters, never events.

---

## 19. Novelty / Inventiveness Search

A preliminary search was conducted on Google Patents, Espacenet, IEEE Xplore, and Google Scholar.

| S.No | Reference | Existing Idea | Our Invention |
|---|---|---|---|
| 1 | Generic auditd/EDR stacks | Host command logging, raw content | Hash-only commands via PSI, healthcare context, sensor fusion |
| 2 | MPU-6050 tamper-evident enclosure patents | Local physical-only alarm | Physical event is one dimension in a fused ML vector with host data |
| 3 | Liu et al., "Isolation Forest" (ICDM 2008) | General anomaly algorithm | Applied to cross-layer medical fusion features with criticality weighting |
| 4 | PSI literature (OPRF, Meadows) | Privacy-preserving set membership | Used as the primary command-safety check in a medical EDR |
| 5 | UEBA products (generic) | User baselines from raw logs | Role/shift insider baselines from hashed + sensor features, HIPAA-safe |
| 6 | Hospital asset-tracking (RFID/BLE) | Where is the device? | Is the device currently under attack or pre-failure? |
| 7 | XAI-for-security literature | Post-hoc explanations of black-box IDS | XAI paragraph that fuses physical + digital contributors for clinicians |

No prior art combining all of (hash-only command telemetry, MEMS+acoustic+magnetic sensor fusion, Isolation Forest, device-criticality-weighted risk, XAI, and healthcare-role insider baselining) was found.

---

## 20. Non-Obviousness to a Person of Average Skill

**No.** A person of average skill in either (a) hospital IT/EDR or (b) IoT tamper-sensor design would not arrive at this invention with public-domain knowledge, for the following reasons:

- EDR engineers do not typically design MEMS mounting schemes or integrate sound/magnetic front ends; they live in the log-analysis world.
- IoT sensor engineers do not typically design PSI pipelines, Linux host agents, or role-aware ML baselines.
- The inventive leap is the **temporal fusion feature-vector construction**, which requires insight from both domains plus an ML-engineering sensibility for how Isolation Forest reacts to mixed-layer features, plus clinical domain knowledge of device criticality, plus a privacy-engineering insight to keep the whole thing hash-only.
- The specific decision to PSI-check commands *before* ML (to short-circuit known-bad) while still feeding the same events into ML (to catch the unknown-unknown) is a non-obvious architectural choice.

---

## 21. Broad Workable Parameter Ranges

| Parameter | Minimum | Typical | Maximum |
|---|---|---|---|
| Agent batch size (`AGENT_BATCH_SIZE`) | 1 | 50 | 1000 |
| Agent send interval (`AGENT_SEND_INTERVAL_SECONDS`) | 1 s | 30 s | 600 s |
| Engine alert threshold (`ENGINE_ALERT_THRESHOLD`) | 0 | 50 | 100 |
| Temporal fusion window | 10 s | 120 s | 600 s |
| Isolation Forest `n_estimators` | 50 | 200 | 1000 |
| Isolation Forest `contamination` | 0.001 | 0.02 | 0.2 |
| MPU-6050 accel clip | ±2 g | ±16 g | ±16 g |
| MPU-6050 gyro clip | ±250 °/s | ±2000 °/s | ±2000 °/s |
| Device criticality weight | 1.0 (kiosk) | 1.5 (fridge) | 2.5 (ICU ventilator, narcotics) |
| PSI threat set size | 10² | 10⁵ | 10⁸ |
| Sensor sampling rate | 1 Hz | 10 Hz | 1 kHz |
| Model retraining interval | 1 h | 24 h | 30 d |

---

## 22. Commercialization Data

**Potential commercial partners / licensees (indicative — to be verified by the inventors):**

1. **GE HealthCare** — 3200 N Grandview Blvd, Waukesha, WI 53188, USA. Major ventilator / patient-monitor OEM with existing hospital-IT footprint.
2. **Philips Healthcare** — Philips Center, Amstelplein 2, 1096 BC Amsterdam, Netherlands. Strong interest in connected-care cybersecurity.
3. **Medtronic plc** — 20 Lower Hatch Street, Dublin 2, Ireland. Infusion pumps and drug-delivery security.
4. **Siemens Healthineers AG** — Henkestraße 127, 91052 Erlangen, Germany. Diagnostic imaging fleet and hospital IT security services.
5. **Wipro GE Healthcare / HCL Healthcare / Tata Elxsi** — India-based healthcare-IT integrators interested in HIPAA-compatible hospital deployments.

**Short marketing profile.** *MedGuard Threat Engine* is the first cross-layer, privacy-preserving threat-detection and insider-risk platform purpose-built for hospitals. Unlike generic EDRs, it never sees raw commands; unlike physical alarms, it understands the host behind the device; unlike static ACL tools, it learns per-role baselines. One dashboard, one model, HIPAA/GDPR/DPDP-friendly by construction, commodity-sensor hardware, and explainable alerts clinicians can act on without a data scientist in the loop.

---

## 23. Market Potential

| Year | Estimated Market Size (Healthcare Cybersecurity) | Growth Drivers | Notable Existing Devices / Players |
|------|--------------------------------------------------|----------------|-------------------------------------|
| 2024 | ~USD 20 B | Ransomware on hospitals; HIPAA/GDPR enforcement | Claroty, Medigate (Claroty xDome), Cynerio, Armis |
| 2026 | ~USD 27 B | FDA pre-market cybersecurity requirements for medical devices; EU MDR | Palo Alto IoT Security, Asimily |
| 2028 | ~USD 38 B | Hospital IoT growth; insider-threat regulation | Nozomi, Forescout Medical |
| 2030 | ~USD 52 B | AI-driven threat detection adoption in healthcare | Expanded OEM-embedded offerings |

*(Figures are order-of-magnitude estimates drawn from publicly reported healthcare-cybersecurity market sizing and should be verified by the inventors / Khurana & Khurana analysts before filing.)*

---

## 24. Names of Inventors

1. **Rudra Saxena** — Lead inventor; system architecture, detection engine, PSI, ML, XAI, sensor fusion design.
2. *(To be added by the team — co-inventors responsible for sensor mounting, dashboard, clinical validation, etc.)*

---

## 25. User Information

**a. Potential users of the technology.**
- Hospital IT / SOC teams
- Biomedical engineering departments
- Hospital administrators and compliance officers
- Pharmacy leads (narcotics cabinets, vaccine cold chain)
- ICU and ward nursing leads (as alert consumers via dashboard)
- Medical device OEMs (as an embedded security layer)
- Research labs and pharma manufacturing sites (as a secondary market)

**b. Age group of the end user.** Approximately 22–65 years (working healthcare and IT professionals). No direct interaction with patients.

**c. Expected benefits to the user.**
- Fewer, higher-quality alerts (cross-layer fusion reduces false positives).
- HIPAA/GDPR/DPDP-compatible telemetry out of the box.
- One dashboard instead of three vendors.
- Actionable, explainable alerts understandable by non-ML staff.
- Predictive maintenance side-benefit reduces equipment downtime.
- Deters insider misuse of narcotics and restricted equipment.

**d. Cost advantage vs. available solutions.**
- Uses commodity sensors (~USD 5–15 each) and commodity MCUs (~USD 5–10) vs. proprietary tamper-evident hardware at 10–50× the cost.
- Built on open-source software stack (FastAPI, PostgreSQL, scikit-learn, React) — no per-seat SIEM licensing.
- Replaces EDR + physical-intrusion + asset-tracker stack (three line items) with one.
- Expected per-device deployed cost is estimated to be 40–70 % lower than comparable enterprise healthcare-cybersecurity offerings.

---

## 26. Technology Readiness Level (TRL)

| TRL 1 | TRL 2 | TRL 3 | **TRL 4** | **TRL 5** | TRL 6 | TRL 7 | TRL 8 | TRL 9 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
|  |  |  | ✅ | ✅ (partial) |  |  |  |  |

**Current state:** Technology validated in a lab environment (TRL 4). Partial validation in a relevant (simulated hospital) environment (TRL 5). Next milestone: TRL 6 — demonstration in an operational hospital pilot ward.

---

## 27. Additional Notes / Remarks

- The privacy property of the invention is enforced at the **schema level** (`shared/event_schema.json`): the schema for a `command` event has no field for raw command text, so a misconfigured agent *cannot* accidentally leak raw commands. This is an important defensive-design point for regulators.
- The engine is model-agnostic: Isolation Forest is the current implementation, but the same fusion + PSI + XAI scaffolding accepts any anomaly scorer (autoencoder, LOF, one-class SVM). Claim language has been drafted accordingly.
- The system deliberately does **not** attempt intent inference on staff. It detects *operational sequences* out of baseline, not *people*. This framing is intentional and should be preserved in the patent language for ethical and regulatory reasons.
- Existing base platform artifacts (code, tests, Docker stack) can be relied upon as reduction-to-practice evidence during prosecution.

---

*End of disclosure.*
