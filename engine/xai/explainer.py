"""Explainable AI: human-readable explanations from risk score, PSI result, and event context."""
from typing import Any


def explain(
    risk_score: float,
    in_threat_set: bool,
    contributing_factors: list[str],
    event_source: str,
    event_context: dict[str, Any] | None = None,
) -> str:
    ctx = event_context or {}
    payload = ctx.get("payload") or {}
    user = ctx.get("user", "unknown")
    machine = ctx.get("machine_id", "unknown")
    source = ctx.get("source") or event_source

    if in_threat_set:
        return _explain_psi(user, machine, payload)

    if risk_score >= 80:
        severity = "HIGH"
        intro = f"[{severity}] Highly anomalous activity detected"
    elif risk_score >= 50:
        severity = "MEDIUM"
        intro = f"[{severity}] Moderately suspicious activity detected"
    elif risk_score >= 20:
        severity = "LOW"
        intro = f"[{severity}] Minor deviation from baseline"
    else:
        return f"Normal activity by {user} on {machine}. No anomalies detected."

    details = _build_details(source, user, machine, payload, ctx)
    factor_text = _format_factors(contributing_factors)

    parts = [f"{intro} for user '{user}' on {machine}."]
    if details:
        parts.append(details)
    if factor_text:
        parts.append(f"Contributing factors: {factor_text}.")
    parts.append(f"Risk score: {risk_score:.0f}/100.")

    return " ".join(parts)


def _explain_psi(user: str, machine: str, payload: dict) -> str:
    cmd_hash = payload.get("command_hash", "")[:12]
    cmd_len = payload.get("command_length")
    parts = [
        f"[CRITICAL] User '{user}' on {machine} executed a command that matches a known malicious hash in the threat database (PSI).",
    ]
    if cmd_hash:
        parts.append(f"Command hash prefix: {cmd_hash}…")
    if cmd_len:
        parts.append(f"Command length: {cmd_len} characters.")
    parts.append("Immediate investigation recommended.")
    return " ".join(parts)


def _build_details(source: str, user: str, machine: str, payload: dict, ctx: dict) -> str:
    ts = ctx.get("timestamp")
    hour = _get_hour(ts)

    if source == "auth":
        action = payload.get("action", "unknown")
        success = payload.get("success")
        service = payload.get("service", "unknown")
        time_note = f" at {hour:02d}:00 UTC" if hour is not None else ""
        if success is False:
            return (
                f"Failed {action} attempt via {service}{time_note}. "
                f"Repeated authentication failures may indicate brute-force or credential-stuffing attacks."
            )
        return f"Successful {action} via {service}{time_note}."

    if source == "command":
        cmd_len = payload.get("command_length")
        time_note = f" at {hour:02d}:00 UTC" if hour is not None else ""
        parts = [f"Command execution{time_note}."]
        if cmd_len and cmd_len > 100:
            parts.append(f"Command length ({cmd_len} chars) is unusually long, which may indicate obfuscation or encoded payloads.")
        return " ".join(parts)

    if source == "process":
        exe = payload.get("exe", "unknown")
        argv = payload.get("argv") or []
        pid = payload.get("pid")
        time_note = f" at {hour:02d}:00 UTC" if hour is not None else ""
        parts = [f"Process '{exe}' (PID {pid}) spawned{time_note}."]
        suspicious_bins = {"nc", "ncat", "nmap", "socat", "curl", "wget", "python", "perl", "ruby", "base64"}
        exe_name = exe.rsplit("/", 1)[-1] if exe else ""
        if exe_name in suspicious_bins:
            parts.append(f"'{exe_name}' is commonly used in post-exploitation and lateral movement.")
        if exe.startswith("/tmp") or exe.startswith("/var/tmp") or exe.startswith("/dev/shm"):
            parts.append(f"Executable running from a world-writable directory ({exe}) — often associated with malware or unauthorized scripts.")
        if any("miner" in a.lower() or "xmrig" in a.lower() for a in argv):
            parts.append("Command-line arguments suggest cryptocurrency mining activity.")
        if any(a in ("-e", "--exec") for a in argv):
            parts.append("Arguments include an exec flag, which may indicate a reverse shell.")
        return " ".join(parts)

    return ""


def _format_factors(factors: list[str]) -> str:
    if not factors:
        return ""
    readable = []
    for f in factors[:5]:
        f = f.replace("_", " ")
        readable.append(f)
    return "; ".join(readable)


def _get_hour(ts: Any) -> int | None:
    if hasattr(ts, "hour"):
        return ts.hour
    if isinstance(ts, str):
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.hour
        except Exception:
            pass
    return None
