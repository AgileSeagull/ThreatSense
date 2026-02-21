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

const POLL_MS = 5000; // Auto-refresh every 5s when demo agents are running
const CHART_COLORS = ['#dc2626', '#ea580c', '#ca8a04', '#16a34a', '#2563eb', '#7c3aed', '#db2777', '#0d9488'];

function riskToLevel(risk: number): number {
  return Math.min(12, Math.max(1, Math.round(risk / (100 / 12))));
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
      setTechniqueSeries(techniqueRes.series ?? []);
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

  const recentAlerts = alerts.slice(0, 10);

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-gray-500">Loading dashboard…</p>
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

  return (
    <div className="space-y-6">
      <p className="text-xs text-gray-400">Auto-refreshing every {POLL_MS / 1000}s</p>
      {/* KPIs - only meaningful metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <p className="text-sm text-gray-500 uppercase tracking-wide">Processed events</p>
          <p className="text-2xl font-bold text-gray-900">{stats?.total ?? 0}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <p className="text-sm text-gray-500 uppercase tracking-wide">Total alerts</p>
          <p className="text-2xl font-bold text-gray-900">{stats?.total_alerts ?? 0}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <p className="text-sm text-gray-500 uppercase tracking-wide">Critical alerts (risk ≥ 83)</p>
          <p className="text-2xl font-bold text-red-600">{stats?.level_12_plus_alerts ?? 0}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <p className="text-sm text-gray-500 uppercase tracking-wide">Auth failures</p>
          <p className="text-2xl font-bold text-gray-900">{stats?.authentication_failure ?? 0}</p>
        </div>
      </div>

      {/* Row 1: Alerts over time + Alerts by type */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-800 mb-1">Alerts over time</h2>
          <p className="text-xs text-gray-500 mb-3">Hourly buckets</p>
          <div className="h-[260px]">
            {alertsOverTimeData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={alertsOverTimeData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="time" tick={{ fontSize: 10 }} stroke="#9ca3af" />
                  <YAxis tick={{ fontSize: 11 }} stroke="#9ca3af" allowDecimals={false} />
                  <Tooltip />
                  <Area type="monotone" dataKey="count" name="Alerts" stroke="#2563eb" fill="#2563eb" fillOpacity={0.4} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-400 text-sm">No alerts in this period</div>
            )}
          </div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-800 mb-3">Alerts by type</h2>
          <div className="h-[260px] flex items-center justify-center">
            {techniqueSeries.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={techniqueSeries}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={90}
                    paddingAngle={2}
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {techniqueSeries.map((_, i) => (
                      <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-400 text-sm">No alerts by type yet</p>
            )}
          </div>
        </div>
      </div>

      {/* Row 2: Top agents + Recent alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-800 mb-3">Top agents by alert count</h2>
          <div className="h-[260px] flex items-center justify-center">
            {topAgentsSeries.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topAgentsSeries} layout="vertical" margin={{ top: 8, right: 24, left: 8, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="name" width={80} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="value" name="Alerts" fill="#2563eb" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-400 text-sm">No agent data yet</p>
            )}
          </div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-800 mb-3">Recent alerts</h2>
          <div className="min-h-[260px]">
            {recentAlerts.length === 0 ? (
              <div className="flex items-center justify-center h-[240px] text-gray-400 text-sm">No recent alerts</div>
            ) : (
              <ul className="space-y-2">
                {recentAlerts.map((alert) => {
                  const level = riskToLevel(alert.risk_score);
                  return (
                    <li key={alert.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                      <div className="min-w-0 flex-1">
                        <Link to={`/alerts/${alert.id}`} className="text-blue-600 hover:underline font-medium truncate block">
                          {alert.event_type} · {alert.user}@{alert.machine_id}
                        </Link>
                        <p className="text-xs text-gray-500 truncate" title={alert.explanation ?? undefined}>
                          {alert.explanation ?? '—'}
                        </p>
                      </div>
                      <div className="ml-2 flex items-center gap-2 shrink-0">
                        <span className="font-mono text-sm font-medium text-gray-700">{Math.round(alert.risk_score)}</span>
                        <span className="text-xs text-gray-400">L{level}</span>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
          {alerts.length > 10 && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <Link to="/alerts" className="text-sm text-blue-600 hover:underline">View all {alerts.length} alerts →</Link>
            </div>
          )}
        </div>
      </div>

      {/* Security alerts table */}
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-sm font-semibold text-gray-800">Security alerts</h2>
          <Link to="/alerts" className="text-sm text-blue-600 hover:underline">View all</Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left py-3 px-4 font-medium text-gray-700">Time</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Machine</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">User</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Type</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Risk</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Description</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Detail</th>
              </tr>
            </thead>
            <tbody>
              {alerts.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-gray-500">
                    No alerts. Run the seed script or the agent to generate data.
                  </td>
                </tr>
              ) : (
                alerts.slice(0, 20).map((alert) => {
                  return (
                    <tr key={alert.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-2 px-4 text-gray-600">
                        {new Date(alert.timestamp).toLocaleDateString()} {new Date(alert.timestamp).toLocaleTimeString(undefined, { hour12: false, hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td className="py-2 px-4 text-gray-700">{alert.machine_id}</td>
                      <td className="py-2 px-4 text-gray-700">{alert.user}</td>
                      <td className="py-2 px-4 text-gray-700">{alert.event_type}</td>
                      <td className="py-2 px-4 font-mono font-medium">{Math.round(alert.risk_score)}</td>
                      <td className="py-2 px-4 text-gray-600 max-w-xs truncate" title={alert.explanation ?? undefined}>
                        {alert.explanation ?? '—'}
                      </td>
                      <td className="py-2 px-4">
                        <Link to={`/alerts/${alert.id}`} className="text-blue-600 hover:underline">#{alert.id}</Link>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
