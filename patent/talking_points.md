# Patent Presentation — Speaking Script
**Total Time: 5 minutes**

---

## Slide 1 — Title ⏱ ~20s

Good morning. I'm Vishal Dev Verma, and along with my co-inventors Rudra Saxena and Rohan Sharma, I'll be presenting our patent application — **System and Method for Cross-Layer Multi-Modal Threat Detection in Healthcare Environments.** This is a privacy-preserving platform that detects both physical and digital threats in hospitals using sensor fusion, hashed monitoring, and explainable AI. We've validated it at TRL 4 to 5 in a simulated hospital setup. Let me start with the problem.

---

## Slide 2 — Problem Statement ⏱ ~35s

Hospitals are a very unique environment. They run life-critical equipment — ventilators, infusion pumps, narcotics cabinets — where a security breach can directly harm patients.

Now these environments face two types of threats at the same time. On the physical side, someone could tamper with a medical device, access a cabinet without authorization, or displace equipment. On the digital side, there are unauthorized logins, malicious commands, privilege escalation, and insider policy violations.

And here's the real constraint — you cannot just send raw command logs and patient-adjacent data to a cloud server. That violates HIPAA, GDPR, and India's DPDP Act. So any solution we build has to be privacy-preserving by design.

So with that context, let's look at what solutions already exist and where they fall short.

---

## Slide 3 — Limitations of Existing Approaches ⏱ ~30s

As you can see in this table, we surveyed six categories of existing technologies.

Traditional EDR tools ship raw commands to the cloud and have zero awareness of what's happening in the physical world. Physical security systems like CCTV and door sensors work in complete isolation — they don't talk to the host systems at all. Rule-based insider threat tools use static access control lists, so they can't detect when a legitimate credential is used in an illegitimate pattern — like a technician logging in at 2 AM on their day off. And ML-based IDS systems produce opaque scores that clinical staff simply cannot understand or act on.

The key gap is this — no existing solution fuses physical and digital data at the feature-vector level while also preserving privacy and giving explainable alerts. That's exactly what our invention addresses.

---

## Slide 4 — Proposed Invention ⏱ ~40s

Our invention is a unified, cross-layer threat engine that fuses physical and digital telemetry under a single anomaly model, with privacy built in by construction.

It has four core components. First, an Endpoint Agent that runs on each Linux host. It monitors authentication events, processes, and commands — but it only transmits SHA-256 hashes of commands, never the raw text. Second, a Sensor Layer made of inexpensive hardware — a gyroscope and accelerometer for tamper detection, a sound sensor, and a magnetic sensor for cabinet and door events. Third, the Detection Engine — this is where Private Set Intersection checks the hashes, Isolation Forest does unsupervised anomaly scoring, and the XAI pipeline generates explanations. And fourth, a Web Dashboard that shows real-time alerts with human-readable risk scores.

What sets this apart is — raw commands never leave the endpoint, physical and digital events are fused at the feature-vector level before scoring, and the explanations are readable by clinical staff without needing a data scientist.

Now let me show you how these components are connected.

---

## Slide 5 — System Architecture ⏱ ~35s

This diagram shows the end-to-end data flow. On the left, we have two data sources — the Endpoint Agent sending authentication, command hash, and process events, and the Hardware Sensors sending gyroscope, sound, and magnetic readings.

Both feed into the Detection Engine Pipeline, which has four stages. First, Ingest and Validate — every event is checked against a unified JSON schema. Then, the PSI Check does set-membership testing on command hashes against a known-threat database. Next, the Isolation Forest performs unsupervised anomaly scoring. And finally, the XAI Explainer generates a plain-English explanation of the alert.

Results are stored in PostgreSQL and pushed to the Web Dashboard for real-time monitoring.

Two important design points here. Privacy is enforced at the schema level — the command event type physically cannot carry raw text, only a hash. And all event types — auth, command, process, sensor — go through the same unified schema, which keeps the pipeline clean and consistent.

Now, what makes this invention novel?

---

## Slide 6 — Novelty and Inventive Step ⏱ ~30s

No prior art combines all of these elements in a single system, and that combination is our inventive step.

First — cross-layer temporal fusion is a first-class feature. Physical and digital events are fused at the feature-vector level before ML scoring, not just displayed side by side in a dashboard.

Second — privacy is structurally enforced through hash-only command telemetry using PSI. It's not a policy someone might bypass — it's baked into the architecture.

Third — device-criticality-weighted risk scoring. The same anomaly gets scored differently depending on where it happens. A suspicious event on an ICU ventilator gets a two-times multiplier compared to a lobby kiosk.

Fourth — explainable AI for non-technical audiences. The system outputs clinician-readable paragraphs that cite both physical and digital contributors to the alert.

And we also do role and shift-aware insider baselining — detecting behavioral pattern deviations, not identity.

Let me show you how this fusion actually works with a concrete example.

---

## Slide 7 — Cross-Layer Temporal Fusion ⏱ ~40s

This is the heart of our invention. Let me walk you through a real scenario.

Imagine it's 2 AM. A narcotics cabinet opens — the magnetic sensor triggers at time zero. Three seconds later, there's a sound burst — maybe a latch or a drawer being pulled. At 8 seconds, an authentication event appears — someone logging into the host near that cabinet. And at 11 seconds, a command is executed that matches a known sudoers-tamper pattern.

Our system collects all these events within a 120-second sliding window per device and fuses them into a single joint feature vector — capturing the temporal and cross-layer correlation.

The Isolation Forest scores this as a raw anomaly of 41. But because this is a narcotics cabinet with a criticality multiplier of 2.2, the final risk score becomes 90 out of 100.

And the system generates this explanation — "Narcotics cabinet opened at 02:14. Off-shift tech logged in 8 seconds later. Command matches known sudoers-tamper. Recommended action — revoke session, page pharmacy lead."

Now here's the key insight — a pure EDR would only see a mildly suspicious command. A pure physical alarm would see a routine cabinet opening. Only our fused engine connects these dots and produces the correct high-severity alert.

Based on these innovations, let me outline our patent claims.

---

## Slide 8 — Patent Claims ⏱ ~25s

We have three independent claims. Claim 1 is our System Claim — it covers the architecture: the endpoint agent transmitting SHA-256 hashes, the physical sensors, and the detection engine with the unified schema. Claim 2 is our Method Claim — covering the five-step process of collecting, fusing, scoring, and explaining threats. Claim 3 is a Computer-Readable Medium claim covering the software.

We also have five dependent claims — covering the temporal fusion window, PSI-based hash matching, XAI natural-language generation, role and shift-aware baselining, and federated multi-hospital deployment.

Let me now highlight the practical advantages and market opportunity.

---

## Slide 9 — Advantages and Market Potential ⏱ ~25s

On the advantages side — privacy is by construction, meaning HIPAA, GDPR, and DPDP compliance is built into the architecture. Cross-layer context gives us a lower false-positive rate because we suppress anomalies that look suspicious in one layer but are normal in the full picture. The XAI output reduces mean time to action because staff can understand alerts without a data scientist. And the cost is low — we use commodity sensors costing 5 to 15 dollars each, and this single platform replaces three separate vendor products.

On the market side, healthcare cybersecurity is projected to grow from about 20 billion dollars in 2024 to over 50 billion by 2030, driven by ransomware attacks, FDA cyber requirements, and IoT proliferation in hospitals.

Let me wrap up.

---

## Slide 10 — Summary and Conclusion ⏱ ~20s

To conclude — our invention is the first cross-layer, privacy-preserving, explainable threat detection platform purpose-built for healthcare.

We meet all three patentability criteria. Novelty — no prior art combines these elements. Inventive step — this required cross-domain expertise spanning cybersecurity, IoT, machine learning, and clinical workflow. And industrial applicability — validated at TRL 4 to 5 with commodity hardware and a clear path to deployment.

Going forward, we plan a clinical pilot in an operational hospital ward and independent red-team testing, with an expected 18 to 25 percent F1 improvement from the fusion approach.

Thank you. We're happy to take your questions.

---

## ⏱ Time Summary

| Slide | Time |
|:---:|:---:|
| 1 — Title | ~20s |
| 2 — Problem | ~35s |
| 3 — Limitations | ~30s |
| 4 — Proposed Invention | ~40s |
| 5 — Architecture | ~35s |
| 6 — Novelty | ~30s |
| 7 — Cross-Layer Fusion | ~40s |
| 8 — Claims | ~25s |
| 9 — Advantages & Market | ~25s |
| 10 — Conclusion | ~20s |
| **Total** | **~5 min** |
