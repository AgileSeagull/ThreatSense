import { useEffect, useState, useCallback } from 'react';
import { api } from '../api/client';
import type { ProcessedEvent } from '../types/api';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, BarChart, Bar, Cell,
} from 'recharts';

const POLL_MS = 5000;
const VISIBLE_ROWS = 10;

type P = Record<string, unknown>;

/* ── Helpers ─────────────────────────────────────────── */

function threatColor(score: number) {
  if (score >= 80) return 'bg-red-100 text-red-800';
  if (score >= 50) return 'bg-orange-100 text-orange-800';
  if (score >= 25) return 'bg-amber-100 text-amber-800';
  return 'bg-teal-50 text-teal-800';
}

function threatBorderColor(score: number) {
  if (score >= 80) return 'border-l-red-500';
  if (score >= 50) return 'border-l-orange-400';
  if (score >= 25) return 'border-l-amber-400';
  return 'border-l-teal-400';
}

function sensorLabel(sType: string) {
  if (sType === 'gyro') return 'Equipment Integrity (MPU-6050)';
  if (sType === 'sound') return 'Acoustic Detection (HW-485)';
  if (sType === 'magnetic') return 'Secure Access Monitor (HW-509)';
  return sType;
}

function sensorDescription(sType: string) {
  if (sType === 'gyro') return 'Detects physical tampering, impact, displacement, and abnormal vibration of medical/secured equipment.';
  if (sType === 'sound') return 'Detects glass breaks, explosions, sustained alarms, and repeated intrusion-related sound bursts.';
  if (sType === 'magnetic') return 'Monitors medication cabinets, server enclosures, and restricted doors for unauthorised access.';
  return '';
}

function shortTime(iso: string) {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function StatusPill({ unsafe }: { unsafe: boolean }) {
  return unsafe
    ? <span className="px-2 py-0.5 rounded text-xs font-semibold bg-red-100 text-red-800 border border-red-200">Anomaly</span>
    : <span className="px-2 py-0.5 rounded text-xs font-semibold bg-teal-50 text-teal-700 border border-teal-200">Normal</span>;
}

/* ── Critical Equipment Alerts ───────────────────────── */

interface RiskySensor {
  key: string;
  machine_id: string;
  sensor_id: string;
  sensor_type: string;
  max_risk: number;
  unsafe_count: number;
  total_count: number;
  latest_reason: string;
  latest_explanation: string | null;
  factors: string[];
}

function buildRiskySensors(events: ProcessedEvent[]): RiskySensor[] {
  const map = new Map<string, RiskySensor>();
  for (const ev of events) {
    const p = (ev.payload ?? {}) as P;
    const sid = String(p.sensor_id ?? 'unknown');
    const key = `${ev.machine_id}::${sid}`;
    const isUnsafe = p.status === 'unsafe';

    if (!map.has(key)) {
      map.set(key, {
        key,
        machine_id: ev.machine_id,
        sensor_id: sid,
        sensor_type: String(p.sensor_type ?? ''),
        max_risk: ev.risk_score,
        unsafe_count: 0,
        total_count: 0,
        latest_reason: '',
        latest_explanation: null,
        factors: [],
      });
    }
    const entry = map.get(key)!;
    entry.total_count++;
    if (isUnsafe) entry.unsafe_count++;

    if (ev.risk_score > entry.max_risk || (isUnsafe && !entry.latest_reason)) {
      entry.max_risk = Math.max(entry.max_risk, ev.risk_score);
      if (isUnsafe && p.reason) entry.latest_reason = String(p.reason);
      if (ev.explanation) entry.latest_explanation = ev.explanation;
      if (ev.contributing_factors?.length) entry.factors = ev.contributing_factors;
    }
  }
  return [...map.values()]
    .sort((a, b) => b.max_risk - a.max_risk || b.unsafe_count - a.unsafe_count)
    .slice(0, 5);
}

function CriticalEquipmentAlerts({ events }: { events: ProcessedEvent[] }) {
  const risky = buildRiskySensors(events);
  if (risky.length === 0) return null;

  return (
    <div className="space-y-3">
      <div>
        <h2 className="text-base font-semibold text-gray-800">Critical Equipment Alerts</h2>
        <p className="text-xs text-gray-500">Sensors with the highest threat activity — requires immediate review</p>
      </div>
      <div className="grid grid-cols-1 gap-3">
        {risky.map((s, i) => (
          <div
            key={s.key}
            className={`bg-white border-l-4 ${threatBorderColor(s.max_risk)} border border-gray-200 rounded-lg p-4`}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-bold text-gray-400">#{i + 1}</span>
                  <span className="font-semibold text-gray-800 text-sm">{sensorLabel(s.sensor_type)}</span>
                  <span className="font-mono text-xs text-gray-400">{s.sensor_id}</span>
                  <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">Device: {s.machine_id}</span>
                </div>

                {s.latest_reason && (
                  <p className="mt-1.5 text-sm text-red-700 font-medium">{s.latest_reason}</p>
                )}
                {s.latest_explanation && (
                  <p className="mt-1 text-sm text-gray-600 italic">{s.latest_explanation}</p>
                )}
                {s.factors.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    <span className="text-xs text-teal-700 font-semibold mr-1">Clinical Indicators:</span>
                    {s.factors.map((f, j) => (
                      <span key={j} className="px-2 py-0.5 bg-teal-50 text-teal-800 border border-teal-200 rounded text-xs">
                        {f}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="text-right shrink-0 space-y-1">
                <span className={`px-3 py-1 rounded-full text-sm font-bold ${threatColor(s.max_risk)}`}>
                  TI {s.max_risk.toFixed(1)}
                </span>
                <p className="text-xs text-gray-400">
                  {s.unsafe_count} anomalies / {s.total_count} readings
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Equipment Integrity (Gyro) ──────────────────────── */

function EquipmentIntegritySection({ events }: { events: ProcessedEvent[] }) {
  const [expanded, setExpanded] = useState(false);
  const sorted = [...events].reverse();
  const chartData = sorted.map(ev => {
    const p = (ev.payload ?? {}) as P;
    return {
      time: shortTime(ev.timestamp),
      ax: Number(p.ax ?? 0),
      ay: Number(p.ay ?? 0),
      az: Number(p.az ?? 0),
      gx: Number(p.gx ?? 0),
      gy: Number(p.gy ?? 0),
      gz: Number(p.gz ?? 0),
    };
  });

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-base font-semibold text-gray-800">Equipment Integrity Monitor (MPU-6050)</h3>
        <p className="text-xs text-gray-500">{sensorDescription('gyro')}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Accelerometer */}
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Motion Acceleration (g)</h4>
          <p className="text-xs text-gray-400 mb-3">Normal: aX≈0, aY≈0, aZ≈9.81 — Spikes indicate physical impact or tampering</p>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="time" tick={{ fontSize: 10 }} stroke="#9ca3af" />
              <YAxis tick={{ fontSize: 10 }} stroke="#9ca3af" />
              <Tooltip />
              <Legend iconSize={8} />
              <Line type="monotone" dataKey="ax" stroke="#ef4444" dot={false} name="aX" strokeWidth={1.5} />
              <Line type="monotone" dataKey="ay" stroke="#22c55e" dot={false} name="aY" strokeWidth={1.5} />
              <Line type="monotone" dataKey="az" stroke="#3b82f6" dot={false} name="aZ" strokeWidth={1.5} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Gyroscope */}
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Rotational Velocity (°/s)</h4>
          <p className="text-xs text-gray-400 mb-3">Normal: all axes ≈ 0 — Elevated readings indicate rotation or sustained vibration</p>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="time" tick={{ fontSize: 10 }} stroke="#9ca3af" />
              <YAxis tick={{ fontSize: 10 }} stroke="#9ca3af" />
              <Tooltip />
              <Legend iconSize={8} />
              <Line type="monotone" dataKey="gx" stroke="#f97316" dot={false} name="gX" strokeWidth={1.5} />
              <Line type="monotone" dataKey="gy" stroke="#a855f7" dot={false} name="gY" strokeWidth={1.5} />
              <Line type="monotone" dataKey="gz" stroke="#06b6d4" dot={false} name="gZ" strokeWidth={1.5} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Readings table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
        <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Reading Log</h4>
        </div>
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-xs font-semibold text-gray-400 uppercase tracking-wide">
              <th className="px-3 py-2 text-left">Time</th>
              <th className="px-3 py-2 text-left">Device</th>
              <th className="px-3 py-2 text-center">Status</th>
              <th className="px-3 py-2 text-right">aX (g)</th>
              <th className="px-3 py-2 text-right">aY (g)</th>
              <th className="px-3 py-2 text-right">aZ (g)</th>
              <th className="px-3 py-2 text-right">gX (°/s)</th>
              <th className="px-3 py-2 text-right">gY (°/s)</th>
              <th className="px-3 py-2 text-right">gZ (°/s)</th>
              <th className="px-3 py-2 text-left">Clinical Finding</th>
              <th className="px-3 py-2 text-right">TI</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {(expanded ? events : events.slice(0, VISIBLE_ROWS)).map(ev => {
              const p = (ev.payload ?? {}) as P;
              const unsafe = p.status === 'unsafe';
              return (
                <tr key={ev.id} className={unsafe ? 'bg-red-50 hover:bg-red-100' : 'hover:bg-slate-50'}>
                  <td className="px-3 py-2 text-gray-400 text-xs whitespace-nowrap">{shortTime(ev.timestamp)}</td>
                  <td className="px-3 py-2 font-mono text-xs text-gray-500">{ev.machine_id}</td>
                  <td className="px-3 py-2 text-center"><StatusPill unsafe={unsafe} /></td>
                  <td className="px-3 py-2 text-right font-mono text-xs">{Number(p.ax ?? 0).toFixed(3)}</td>
                  <td className="px-3 py-2 text-right font-mono text-xs">{Number(p.ay ?? 0).toFixed(3)}</td>
                  <td className="px-3 py-2 text-right font-mono text-xs">{Number(p.az ?? 0).toFixed(3)}</td>
                  <td className="px-3 py-2 text-right font-mono text-xs">{Number(p.gx ?? 0).toFixed(1)}</td>
                  <td className="px-3 py-2 text-right font-mono text-xs">{Number(p.gy ?? 0).toFixed(1)}</td>
                  <td className="px-3 py-2 text-right font-mono text-xs">{Number(p.gz ?? 0).toFixed(1)}</td>
                  <td className="px-3 py-2 text-xs text-gray-600 max-w-xs truncate" title={String(p.reason ?? '')}>
                    {String(p.reason ?? '—')}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${threatColor(ev.risk_score)}`}>
                      {ev.risk_score.toFixed(1)}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {events.length > VISIBLE_ROWS && (
          <button
            onClick={() => setExpanded(e => !e)}
            className="w-full py-2 text-xs font-medium text-teal-600 hover:bg-teal-50 border-t border-gray-200"
          >
            {expanded ? 'Show fewer readings' : `Show all ${events.length} readings`}
          </button>
        )}
      </div>
    </div>
  );
}

/* ── Binary sensor (Sound / Magnetic) ───────────────── */

function BinarySensorSection({
  sensorType,
  events,
}: {
  sensorType: 'sound' | 'magnetic';
  events: ProcessedEvent[];
}) {
  const [expanded, setExpanded] = useState(false);
  const sorted = [...events].reverse();
  const chartData = sorted.map(ev => {
    const p = (ev.payload ?? {}) as P;
    return { time: shortTime(ev.timestamp), triggered: p.triggered ? 1 : 0 };
  });

  const triggerCount = events.filter(ev => (ev.payload as P)?.triggered).length;
  const title = sensorLabel(sensorType);
  const desc = sensorDescription(sensorType);
  const detectionLabel = sensorType === 'sound' ? 'Acoustic Event' : 'Access Detected';

  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-center gap-3">
          <h3 className="text-base font-semibold text-gray-800">{title}</h3>
          {triggerCount > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700 border border-red-200 font-semibold">
              {triggerCount} detection{triggerCount !== 1 ? 's' : ''}
            </span>
          )}
        </div>
        <p className="text-xs text-gray-500">{desc}</p>
      </div>

      {/* Detection timeline */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Detection Timeline</h4>
        <p className="text-xs text-gray-400 mb-3">
          Red = {detectionLabel} · Gray = Normal · {triggerCount} / {events.length} triggered
        </p>
        <ResponsiveContainer width="100%" height={130}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="time" tick={{ fontSize: 10 }} stroke="#9ca3af" />
            <YAxis domain={[0, 1]} ticks={[0, 1]} tick={{ fontSize: 10 }} stroke="#9ca3af"
              tickFormatter={v => (v === 1 ? 'ON' : 'OFF')} />
            <Tooltip formatter={(v: number | undefined) => (v === 1 ? detectionLabel : 'Normal')} />
            <Bar dataKey="triggered" name="Status">
              {chartData.map((entry, i) => (
                <Cell key={i} fill={entry.triggered ? '#ef4444' : '#d1fae5'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Readings table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
        <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Detection Log</h4>
        </div>
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-xs font-semibold text-gray-400 uppercase tracking-wide">
              <th className="px-4 py-2 text-left">Time</th>
              <th className="px-4 py-2 text-left">Device</th>
              <th className="px-4 py-2 text-center">Detection Status</th>
              <th className="px-4 py-2 text-left">Clinical Finding</th>
              <th className="px-4 py-2 text-right">Threat Index</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {(expanded ? events : events.slice(0, VISIBLE_ROWS)).map(ev => {
              const p = (ev.payload ?? {}) as P;
              const triggered = !!p.triggered;
              return (
                <tr key={ev.id} className={triggered ? 'bg-red-50 hover:bg-red-100' : 'hover:bg-slate-50'}>
                  <td className="px-4 py-2 text-gray-400 text-xs whitespace-nowrap">{shortTime(ev.timestamp)}</td>
                  <td className="px-4 py-2 font-mono text-xs text-gray-500">{ev.machine_id}</td>
                  <td className="px-4 py-2 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <span className={`w-2.5 h-2.5 rounded-full ${triggered ? 'bg-red-500 animate-pulse' : 'bg-teal-400'}`} />
                      <span className="text-xs">{triggered ? detectionLabel : 'Normal'}</span>
                    </div>
                  </td>
                  <td className="px-4 py-2 text-xs text-gray-600 max-w-sm truncate" title={String(p.reason ?? '')}>
                    {String(p.reason ?? '—')}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${threatColor(ev.risk_score)}`}>
                      {ev.risk_score.toFixed(1)}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {events.length > VISIBLE_ROWS && (
          <button
            onClick={() => setExpanded(e => !e)}
            className="w-full py-2 text-xs font-medium text-teal-600 hover:bg-teal-50 border-t border-gray-200"
          >
            {expanded ? 'Show fewer readings' : `Show all ${events.length} readings`}
          </button>
        )}
      </div>
    </div>
  );
}

/* ── Main page ───────────────────────────────────────── */

export function Sensors() {
  const [events, setEvents] = useState<ProcessedEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [machineFilter, setMachineFilter] = useState('');
  const [limit, setLimit] = useState('200');

  const fetchSensors = useCallback(async () => {
    try {
      setError(null);
      const q: Record<string, string | number> = {
        event_type: 'sensor',
        limit: parseInt(limit) || 200,
      };
      if (machineFilter) q.machine_id = machineFilter;
      const data = await api.activity.list(q);
      setEvents(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load sensor data');
    } finally {
      setLoading(false);
    }
  }, [machineFilter, limit]);

  useEffect(() => {
    fetchSensors();
    const t = setInterval(fetchSensors, POLL_MS);
    return () => clearInterval(t);
  }, [fetchSensors]);

  const gyro = events.filter(e => (e.payload as P)?.sensor_type === 'gyro');
  const sound = events.filter(e => (e.payload as P)?.sensor_type === 'sound');
  const magnetic = events.filter(e => (e.payload as P)?.sensor_type === 'magnetic');
  const anomalyCount = events.filter(e => (e.payload as P)?.status === 'unsafe').length;
  const criticalCount = events.filter(e => e.risk_score >= 80).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Vital Sensor Monitor</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Real-time physical security telemetry — equipment integrity, acoustic detection, and access control
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-end bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-gray-500">Device ID</label>
          <input
            className="border border-gray-300 rounded px-2 py-1.5 text-sm w-48 focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
            placeholder="All devices"
            value={machineFilter}
            onChange={e => setMachineFilter(e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-gray-500">Limit</label>
          <input
            className="border border-gray-300 rounded px-2 py-1.5 text-sm w-24 focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
            type="number"
            min={1}
            max={1000}
            value={limit}
            onChange={e => setLimit(e.target.value)}
          />
        </div>
        <button
          className="px-4 py-2 bg-teal-600 text-white text-sm font-medium rounded hover:bg-teal-500 transition-colors"
          onClick={fetchSensors}
        >
          Apply
        </button>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Equipment Integrity</p>
          <p className="mt-1 text-3xl font-bold text-gray-900">{gyro.length}</p>
          <p className="text-xs text-gray-400 mt-0.5">MPU-6050 readings</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Acoustic Detection</p>
          <p className="mt-1 text-3xl font-bold text-gray-900">{sound.length}</p>
          <p className="text-xs text-gray-400 mt-0.5">HW-485 readings</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Secure Access</p>
          <p className="mt-1 text-3xl font-bold text-gray-900">{magnetic.length}</p>
          <p className="text-xs text-gray-400 mt-0.5">HW-509 readings</p>
        </div>
        <div className={`border rounded-lg p-4 shadow-sm ${anomalyCount > 0 ? 'bg-red-50 border-red-300' : 'bg-white border-gray-200'}`}>
          <p className={`text-xs font-medium uppercase tracking-wide ${anomalyCount > 0 ? 'text-red-600' : 'text-gray-500'}`}>
            Anomaly Readings
          </p>
          <p className={`mt-1 text-3xl font-bold ${anomalyCount > 0 ? 'text-red-700' : 'text-gray-900'}`}>{anomalyCount}</p>
          <p className={`text-xs mt-0.5 ${anomalyCount > 0 ? 'text-red-400' : 'text-gray-400'}`}>
            {criticalCount > 0 ? `${criticalCount} critical` : `of ${events.length} total`}
          </p>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 text-red-800 p-4">{error}</div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-4 border-teal-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : events.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="font-medium">No sensor readings found.</p>
          <p className="text-sm mt-1">Run <code className="bg-gray-100 px-1 rounded">python scripts/sensor_simulator.py</code> to stream live sensor data.</p>
        </div>
      ) : (
        <div className="space-y-10">
          <CriticalEquipmentAlerts events={events} />
          {gyro.length > 0 && <EquipmentIntegritySection events={gyro} />}
          {sound.length > 0 && <BinarySensorSection sensorType="sound" events={sound} />}
          {magnetic.length > 0 && <BinarySensorSection sensorType="magnetic" events={magnetic} />}
        </div>
      )}
    </div>
  );
}
