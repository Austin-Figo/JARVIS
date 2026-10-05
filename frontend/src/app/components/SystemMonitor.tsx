import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { AreaChart, Area, ResponsiveContainer } from 'recharts';
import { Activity, Cpu, Database, Wifi, Thermometer, Zap } from 'lucide-react';
import { getApiBaseUrl, getSystemMetrics, SystemMetrics } from '../services/jarvisApi';

const orb = { fontFamily: 'Orbitron, sans-serif' };
const mono = { fontFamily: 'Share Tech Mono, monospace' };
const raj = { fontFamily: 'Rajdhani, sans-serif' };
type Point = { t: number; v: number };
const initialData = (): Point[] => Array.from({ length: 25 }, (_, i) => ({ t: i, v: 0 }));
const appendPoint = (points: Point[], value: number | null): Point[] => {
  const raw = value ?? 0;
  const previous = points.at(-1)?.v ?? raw;
  // Smooth short-lived telemetry spikes without hiding real changes.
  const smoothed = previous === 0 ? raw : previous * 0.65 + raw * 0.35;
  return [...points.slice(1), { t: Date.now(), v: smoothed }];
};

function MetricCard({ label, value, unit, color, icon, data, progress = value ?? 0 }: { label: string; value: number | null; unit: string; color: string; icon: React.ReactNode; data: Point[]; progress?: number }) {
  return <div className="rounded-xl p-3 flex flex-col gap-2" style={{ background: 'rgba(0, 8, 20, 0.5)', border: `1px solid ${color}25` }}>
    <div className="flex items-center justify-between"><div className="flex items-center gap-2"><div style={{ color }}>{icon}</div><span style={{ ...mono, color: 'rgba(255,255,255,0.5)', fontSize: '10px' }}>{label}</span></div><span style={{ ...orb, color, fontSize: '14px', textShadow: `0 0 8px ${color}` }}>{value === null ? '—' : Math.round(value)}<span style={{ fontSize: '9px', opacity: 0.7 }}>{unit}</span></span></div>
    <div className="h-1 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}><motion.div className="h-full rounded-full" animate={{ width: `${Math.min(100, Math.max(0, progress))}%` }} transition={{ duration: 0.9, ease: 'easeOut' }} style={{ background: `linear-gradient(90deg, ${color}80, ${color})`, boxShadow: `0 0 6px ${color}` }} /></div>
    <div style={{ height: 36 }}><ResponsiveContainer width="100%" height="100%"><AreaChart data={data} margin={{ top: 2, right: 0, bottom: 0, left: 0 }}><defs><linearGradient id={`grad-${label}`} x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor={color} stopOpacity={0.25} /><stop offset="95%" stopColor={color} stopOpacity={0} /></linearGradient></defs><Area type="monotone" dataKey="v" stroke={color} strokeWidth={1.5} fill={`url(#grad-${label})`} dot={false} isAnimationActive={false} /></AreaChart></ResponsiveContainer></div>
  </div>;
}

export function SystemMonitor() {
  const [cpu, setCpu] = useState(initialData);
  const [memory, setMemory] = useState(initialData);
  const [network, setNetwork] = useState(initialData);
  const [gpu, setGpu] = useState(initialData);
  const [latest, setLatest] = useState<SystemMetrics | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let source: EventSource | null = null;
    let fallbackTimer: number | null = null;
    const applyMetrics = (metrics: SystemMetrics) => {
      setCpu(data => appendPoint(data, metrics.cpu_percent)); setMemory(data => appendPoint(data, metrics.memory_percent));
      setNetwork(data => appendPoint(data, metrics.network_mbps)); setGpu(data => appendPoint(data, metrics.gpu_percent));
      setLatest(metrics); setConnected(true);
    };
    const poll = async () => {
      try {
        const metrics = await getSystemMetrics();
        applyMetrics(metrics);
      } catch { setConnected(false); }
    };
    try {
      source = new EventSource(`${getApiBaseUrl()}/api/system/stream`);
      source.onmessage = event => {
        try { applyMetrics(JSON.parse(event.data) as SystemMetrics); } catch { setConnected(false); }
      };
      source.onerror = () => {
        source?.close();
        setConnected(false);
        if (fallbackTimer === null) {
          void poll();
          fallbackTimer = window.setInterval(() => void poll(), 1000);
        }
      };
    } catch {
      void poll();
      fallbackTimer = window.setInterval(() => void poll(), 1000);
    }
    return () => { source?.close(); if (fallbackTimer !== null) window.clearInterval(fallbackTimer); };
  }, []);

  const metrics = [
    { label: 'CPU', value: latest?.cpu_percent ?? null, unit: '%', color: '#00f5ff', icon: <Cpu className="w-3 h-3" />, data: cpu },
    { label: 'MEMORY', value: latest?.memory_percent ?? null, unit: '%', color: '#a855f7', icon: <Database className="w-3 h-3" />, data: memory },
    { label: 'NETWORK', value: latest?.network_mbps ?? null, unit: ' Mbps', color: '#0ea5e9', icon: <Wifi className="w-3 h-3" />, data: network, progress: Math.min(100, (latest?.network_mbps ?? 0) * 10) },
    { label: 'GPU', value: latest?.gpu_percent ?? null, unit: '%', color: '#f59e0b', icon: <Zap className="w-3 h-3" />, data: gpu },
  ];
  const actual = metrics.flatMap(metric => metric.value === null ? [] : [metric.value]);
  const health = Math.round(actual.reduce((sum, value) => sum + value, 0) / actual.length || 0);
  const healthColor = health < 60 ? '#22c55e' : health < 80 ? '#f59e0b' : '#ef4444';
  const uptime = latest?.uptime_seconds ?? 0;
  const uptimeLabel = `${Math.floor(uptime / 3600)}h ${Math.floor((uptime % 3600) / 60)}m`;

  return <div className="flex flex-col h-full gap-3 overflow-hidden">
    <div className="flex items-center justify-between flex-shrink-0"><div className="flex items-center gap-2"><Activity className="w-4 h-4" style={{ color: '#00f5ff' }} /><span style={{ ...orb, color: '#00f5ff', fontSize: '11px', letterSpacing: '0.15em' }}>SYSTEM MONITOR</span></div><div className="flex items-center gap-1.5"><motion.div animate={{ opacity: [1, 0.3, 1] }} transition={{ duration: 1.5, repeat: Infinity }} className="w-1.5 h-1.5 rounded-full" style={{ background: connected ? '#22c55e' : '#ef4444' }} /><span style={{ ...mono, color: connected ? '#22c55e' : '#ef4444', fontSize: '9px' }}>{connected ? 'LIVE' : 'OFFLINE'}</span></div></div>
    <div className="rounded-xl p-3 flex items-center gap-4 flex-shrink-0" style={{ background: 'rgba(0,8,20,0.5)', border: `1px solid ${healthColor}25` }}><div className="relative w-12 h-12 flex-shrink-0"><svg viewBox="0 0 48 48" className="w-full h-full -rotate-90"><circle cx="24" cy="24" r="20" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="4" /><motion.circle cx="24" cy="24" r="20" fill="none" stroke={healthColor} strokeWidth="4" strokeLinecap="round" strokeDasharray={`${2 * Math.PI * 20}`} animate={{ strokeDashoffset: 2 * Math.PI * 20 * (1 - health / 100) }} transition={{ duration: 0.6 }} /></svg><div className="absolute inset-0 flex items-center justify-center"><span style={{ ...orb, color: healthColor, fontSize: '10px' }}>{health}</span></div></div><div className="flex flex-col gap-0.5"><span style={{ ...raj, color: 'rgba(255,255,255,0.7)', fontSize: '13px' }}>System Health</span><span style={{ ...mono, color: 'rgba(255,255,255,0.35)', fontSize: '10px' }}>UPTIME: {uptimeLabel}</span><div className="flex items-center gap-2 mt-0.5"><Thermometer className="w-3 h-3" style={{ color: '#f59e0b' }} /><span style={{ ...mono, color: '#f59e0b', fontSize: '10px' }}>{latest?.temperature_celsius === null || !latest ? 'TEMP N/A' : `${Math.round(latest.temperature_celsius)}°C`}</span></div></div><div className="ml-auto"><span style={{ ...raj, color: healthColor, fontSize: '12px' }}>{connected ? (health < 60 ? 'OPTIMAL' : health < 80 ? 'MODERATE' : 'HIGH LOAD') : 'WAITING'}</span></div></div>
    <div className="grid grid-cols-2 gap-2 flex-1 overflow-y-auto">{metrics.map(metric => <MetricCard key={metric.label} {...metric} />)}</div>
    <div className="rounded-xl p-3 flex-shrink-0" style={{ background: 'rgba(0,8,20,0.5)', border: '1px solid rgba(0,245,255,0.08)' }}><div className="flex items-center justify-between mb-2"><span style={{ ...mono, color: 'rgba(0,245,255,0.6)', fontSize: '10px' }}>LOCAL SERVICES</span></div>{(latest?.processes ?? []).map(process => <div key={process.name} className="flex items-center justify-between py-1" style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}><span style={{ ...mono, color: 'rgba(255,255,255,0.5)', fontSize: '9px' }}>{process.name}</span><span style={{ ...mono, color: '#22c55e', fontSize: '9px' }}>RUNNING</span></div>)}</div>
  </div>;
}
