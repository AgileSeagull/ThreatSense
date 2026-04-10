import { useEffect, useState } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
  BarChart,
  Bar,
} from 'recharts';
import { api } from '../api/client';
import type { Alert } from '../types/api';
import { Link } from 'react-router-dom';
import { RiskBadge } from '../components/RiskBadge';

const POLL_MS = 5000;
const CHART_COLORS = ['#0f766e', '#dc2626', '#ea580c', '#ca8a04', '#2563eb', '#7c3aed', '#db2777', '#0d9488'];

const EVENT_TYPE_LABELS: Record<string, string> = {
  auth: 'Access Control',
  command: 'System Command',
  process: 'System Process',
  sensor: 'Sensor Reading',
};

function ThreatIndexBar({ score }: { score: number }) {
  const pct = Math.min(100, Math.max(0, score));
  const color = score >= 80 ? 'bg-red-500' : score >= 50 ? 'bg-orange-500' : score >= 20 ? 'bg-amber-400' : 'bg-teal-400';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-gray-600 w-8 text-right">{Math.round(score)}</span>
    </div>
  );
}

export function Dashboard() {
  const [stats, setStats] = useState<{
    total: number;
    total_alerts: number;
    level_12_plus_alerts: number;
    authentication_failure: number;
    authentication_success: number;
  } | null>(null);
  const [alertsOverTime, setAlertsOverTime] = useState<{ period: string; [k: string]: string | number }[]>([]);
  const [techniqueSeries, setTechniqueSeries] = useState<{ name: string; value: number }[]>([]);
  const [topAgentsSeries, setTopAgentsSeries] = useState<{ name: string; value: number }[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = async () => {
    try {
      setError(null);
      const [statsRes, overTimeRes, techniqueRes, topRes, alertsRes] = await Promise.all([
        api.dashboard.stats(),
        api.dashboard.alertsOverTime({ interval_minutes: 60 }),
        api.dashboard.alertsByTechnique(),
        api.dashboard.topAgents({ top_n: 5 }),
        api.alerts.list({ limit: 100 }),
      ]);
      setStats(statsRes);
      setAlertsOverTime(overTimeRes.series ?? []);
      // Remap technique names to healthcare labels
      setTechniqueSeries(
        (techniqueRes.series ?? []).map((s) => ({
          ...s,
          name: EVENT_TYPE_LABELS[s.name] ?? s.name,
        }))
      );
      setTopAgentsSeries(topRes.series ?? []);
      setAlerts(Array.isArray(alertsRes) ? alertsRes : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
    const t = setInterval(fetchAll, POLL_MS);
    return () => clearInterval(t);
  }, []);

  const levelKeys = Array.from({ length: 10 }, (_, i) => `level_${i + 3}`);

  const alertsOverTimeData = alertsOverTime.map((row) => {
    const out: Record<string, string | number> = { period: row.period };
    try {
      const d = new Date(row.period as string);
      out.time = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + ' ' + d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
    } catch {
      out.time = String(row.period);
    }
    let total = 0;
    levelKeys.forEach((k) => {
      const v = Number(row[k] ?? 0);
      out[k] = v;
      total += v;
    });
    out.count = total;
    return out;
  });

  const recentAlerts = alerts.slice(0, 8);

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center space-y-2">
          <div className="w-8 h-8 border-4 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-gray-500 text-sm">Initialising clinical monitoring…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 text-red-800 p-4">
        {error}
      </div>
    );
  }

  const criticalAlerts = alerts.filter((a) => a.risk_score >= 80).length;
  const highAlerts = alerts.filter((a) => a.risk_score >= 50 && a.risk_score < 80).length;

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Clinical Security Overview</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Real-time hardware and software threat monitoring for healthcare systems
          </p>
        </div>
        <p className="text-xs text-gray-400 pb-0.5">Auto-refreshing every {POLL_MS / 1000}s</p>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <p className="text-xs text-gray-500 uppercase tracking-wide font-medium">Monitored Events</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{stats?.total ?? 0}</p>
          <p className="text-xs text-gray-400 mt-0.5">Total processed</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <p className="text-xs text-gray-500 uppercase tracking-wide font-medium">Active Incidents</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{stats?.total_alerts ?? 0}</p>
          <p className="text-xs text-gray-400 mt-0.5">Requires review</p>
        </div>
        <div className="bg-white border border-red-200 rounded-lg p-4 shadow-sm bg-red-50">
          <p className="text-xs text-red-600 uppercase tracking-wide font-medium">Critical Incidents</p>
          <p className="text-3xl font-bold text-red-700 mt-1">{stats?.level_12_plus_alerts ?? 0}</p>
          <p className="text-xs text-red-400 mt-0.5">Threat Index ≥ 83</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <p className="text-xs text-gray-500 uppercase tracking-wide font-medium">Access Violations</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{stats?.authentication_failure ?? 0}</p>
          <p className="text-xs text-gray-400 mt-0.5">Unauthorised attempts</p>
        </div>
      </div>

      {/* Severity breakdown strip */}
      {alerts.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <p className="text-xs text-gray-500 uppercase tracking-wide font-medium mb-3">Incident Severity Breakdown</p>
          <div className="flex flex-wrap gap-4">
            {[
              { label: 'Critical', count: criticalAlerts, color: 'bg-red-600', text: 'text-red-700' },
              { label: 'High', count: highAlerts, color: 'bg-orange-500', text: 'text-orange-600' },
              { label: 'Moderate', count: alerts.filter(a => a.risk_score >= 20 && a.risk_score < 50).length, color: 'bg-amber-400', text: 'text-amber-600' },
              { label: 'Low', count: alerts.filter(a => a.risk_score < 20).length, color: 'bg-teal-400', text: 'text-teal-700' },
            ].map(({ label, count, color, text }) => (
              <div key={label} className="flex items-center gap-2">
                <span className={`w-3 h-3 rounded-full ${color}`} />
                <span className={`text-sm font-semibold ${text}`}>{count}</span>
                <span className="text-xs text-gray-500">{label}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-800 mb-1">Incident Frequency</h2>
          <p className="text-xs text-gray-400 mb-3">Alerts per hour — all incident types</p>
          <div className="h-[240px]">
            {alertsOverTimeData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={alertsOverTimeData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="time" tick={{ fontSize: 10 }} stroke="#9ca3af" />
                  <YAxis tick={{ fontSize: 11 }} stroke="#9ca3af" allowDecimals={false} />
                  <Tooltip />
                  <Area type="monotone" dataKey="count" name="Incidents" stroke="#0f766e" fill="#0f766e" fillOpacity={0.25} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-400 text-sm">No incidents in this period</div>
            )}
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-800 mb-1">Incident Classification</h2>
          <p className="text-xs text-gray-400 mb-3">Distribution by event category</p>
          <div className="h-[240px] flex items-center justify-center">
            {techniqueSeries.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={techniqueSeries}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={90}
                    paddingAngle={2}
                    label={({ name, value }) => `${name}: ${value}`}
                    labelLine={false}
                  >
                    {techniqueSeries.map((_, i) => (
                      <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend iconSize={10} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-400 text-sm">No incidents to classify yet</p>
            )}
          </div>
        </div>
      </div>

      {/* Row 2: top devices + recent */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-800 mb-1">High-Risk Devices</h2>
          <p className="text-xs text-gray-400 mb-3">Devices with the most active incidents</p>
          <div className="h-[240px] flex items-center justify-center">
            {topAgentsSeries.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topAgentsSeries} layout="vertical" margin={{ top: 8, right: 24, left: 8, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="name" width={90} tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Bar dataKey="value" name="Incidents" fill="#0f766e" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-400 text-sm">No device data yet</p>
            )}
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-800">Recent Incidents</h2>
            <Link to="/alerts" className="text-xs text-teal-600 hover:underline">View all →</Link>
          </div>
          <div className="min-h-[200px]">
            {recentAlerts.length === 0 ? (
              <div className="flex items-center justify-center h-[200px] text-gray-400 text-sm">No incidents detected</div>
            ) : (
              <ul className="space-y-2">
                {recentAlerts.map((alert) => (
                  <li key={alert.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                    <div className="min-w-0 flex-1 space-y-0.5">
                      <Link to={`/alerts/${alert.id}`} className="text-teal-700 hover:underline font-medium truncate block text-sm">
                        {EVENT_TYPE_LABELS[alert.event_type] ?? alert.event_type} · {alert.user}
                      </Link>
                      <p className="text-xs text-gray-500 truncate font-mono">{alert.machine_id}</p>
                      <p className="text-xs text-gray-400 truncate" title={alert.explanation ?? undefined}>
                        {alert.explanation ?? '—'}
                      </p>
                    </div>
                    <div className="ml-3 shrink-0">
                      <RiskBadge score={alert.risk_score} size="sm" />
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>

      {/* Active Threat Log table */}
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50">
          <div>
            <h2 className="text-sm font-semibold text-gray-800">Active Threat Log</h2>
            <p className="text-xs text-gray-400">All incidents requiring clinical review</p>
          </div>
          <Link to="/alerts" className="text-sm text-teal-600 hover:underline">View all incidents</Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left py-3 px-4 font-medium text-gray-500 text-xs uppercase tracking-wide">Timestamp</th>
                <th className="text-left py-3 px-4 font-medium text-gray-500 text-xs uppercase tracking-wide">Device</th>
                <th className="text-left py-3 px-4 font-medium text-gray-500 text-xs uppercase tracking-wide">Operator</th>
                <th className="text-left py-3 px-4 font-medium text-gray-500 text-xs uppercase tracking-wide">Category</th>
                <th className="text-left py-3 px-4 font-medium text-gray-500 text-xs uppercase tracking-wide">Threat Index</th>
                <th className="text-left py-3 px-4 font-medium text-gray-500 text-xs uppercase tracking-wide">Clinical Finding</th>
                <th className="text-left py-3 px-4 font-medium text-gray-500 text-xs uppercase tracking-wide">Report</th>
              </tr>
            </thead>
            <tbody>
              {alerts.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-gray-400">
                    No incidents detected. Run the sensor simulator or endpoint agent to generate data.
                  </td>
                </tr>
              ) : (
                alerts.slice(0, 20).map((alert) => (
                  <tr key={alert.id} className="border-b border-gray-100 hover:bg-slate-50">
                    <td className="py-2 px-4 text-gray-500 text-xs whitespace-nowrap">
                      {new Date(alert.timestamp).toLocaleDateString()} {new Date(alert.timestamp).toLocaleTimeString(undefined, { hour12: false, hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="py-2 px-4 text-gray-600 font-mono text-xs">{alert.machine_id}</td>
                    <td className="py-2 px-4 text-gray-700">{alert.user}</td>
                    <td className="py-2 px-4">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200">
                        {EVENT_TYPE_LABELS[alert.event_type] ?? alert.event_type}
                      </span>
                    </td>
                    <td className="py-2 px-4 w-32">
                      <ThreatIndexBar score={alert.risk_score} />
                    </td>
                    <td className="py-2 px-4 text-gray-600 max-w-xs truncate text-xs" title={alert.explanation ?? undefined}>
                      {alert.explanation ?? '—'}
                    </td>
                    <td className="py-2 px-4">
                      <Link to={`/alerts/${alert.id}`} className="text-teal-600 hover:underline text-xs">
                        #{alert.id}
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
