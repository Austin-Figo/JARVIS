import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X, Scan, Zap, Eye, Activity, CheckCircle } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { ScanResult, sendCommand } from '../services/jarvisApi';

const orb = { fontFamily: 'Orbitron, sans-serif' };
const mono = { fontFamily: 'Share Tech Mono, monospace' };
const raj = { fontFamily: 'Rajdhani, sans-serif' };

type ScanPhase = 'initializing' | 'scanning' | 'analyzing' | 'complete';

const SCAN_RESULTS = [
  { category: 'NEURAL NETWORK', value: 'Gemini 2.5 — 98.7% accuracy', status: 'optimal' },
  { category: 'SECURITY LAYER', value: 'AES-256 + RSA-4096 — No threats', status: 'secure' },
  { category: 'MEMORY USAGE', value: '6.2 GB / 16 GB — 38% utilized', status: 'optimal' },
  { category: 'NETWORK HEALTH', value: '847ms latency — 1.2 GB/s throughput', status: 'good' },
  { category: 'API ENDPOINTS', value: '4/4 services online — 99.9% uptime', status: 'optimal' },
  { category: 'VOICE ENGINE', value: 'Model v2.3 — 94.2% recognition rate', status: 'good' },
  { category: 'GESTURE MODULE', value: 'Camera feed active — 89.1% confidence', status: 'good' },
  { category: 'DATA INTEGRITY', value: 'All checksums verified — Zero corruption', status: 'secure' },
];

const DATA_POINTS = Array(40).fill(0).map((_, i) => ({
  x: `${(i % 8) * 12 + Math.random() * 4}%`,
  y: `${Math.floor(i / 8) * 20 + Math.random() * 12}%`,
  delay: i * 0.05,
}));

export function ScanningPanel() {
  const { scanningActive, setScanningActive, addNotification } = useApp();
  const [phase, setPhase] = useState<ScanPhase>('initializing');
  const [progress, setProgress] = useState(0);
  const [visibleResults, setVisibleResults] = useState(0);
  const [results, setResults] = useState<ScanResult[]>([]);

  useEffect(() => {
    if (!scanningActive) {
      setPhase('initializing');
      setProgress(0);
      setVisibleResults(0);
      return;
    }

    setPhase('initializing');
    setProgress(8);
    setResults([]);
    let cancelled = false;
    const timers: ReturnType<typeof setTimeout>[] = [];
    const runScan = async () => {
      timers.push(setTimeout(() => !cancelled && setPhase('scanning'), 250));
      timers.push(setTimeout(() => !cancelled && setProgress(35), 400));
      try {
        const response = await sendCommand('scan', 'scanner');
        if (cancelled) return;
        const scanResults = response.data?.scan_results ?? [];
        if (!response.ok || scanResults.length === 0) throw new Error(response.message || 'The scan returned no results.');
        setResults(scanResults);
        setProgress(82);
        setPhase('analyzing');
        timers.push(setTimeout(() => {
          if (cancelled) return;
          setProgress(100);
          setPhase('complete');
          scanResults.forEach((_, index) => timers.push(setTimeout(() => !cancelled && setVisibleResults(value => value + 1), index * 180)));
          addNotification({ type: 'success', title: 'Scan Complete', message: response.message });
        }, 450));
      } catch (error) {
        if (!cancelled) {
          const message = error instanceof Error ? error.message : 'Unable to complete the system scan.';
          setPhase('complete');
          setProgress(100);
          addNotification({ type: 'error', title: 'Scan Failed', message });
        }
      }
    };
    void runScan();
    return () => { cancelled = true; timers.forEach(clearTimeout); };
  }, [scanningActive]);

  const statusColor: Record<ScanResult['status'], string> = {
    optimal: '#22c55e', secure: '#00f5ff', good: '#f59e0b', info: '#0ea5e9', warning: '#f59e0b', critical: '#ef4444',
  };

  return (
    <AnimatePresence>
      {scanningActive && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="fixed inset-0 flex items-center justify-center"
          style={{ zIndex: 200, background: 'rgba(0, 5, 15, 0.92)', backdropFilter: 'blur(8px)' }}
        >
          {/* Close */}
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => setScanningActive(false)}
            className="absolute top-6 right-6 w-10 h-10 rounded-xl flex items-center justify-center cursor-pointer"
            style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)' }}
          >
            <X className="w-5 h-5" style={{ color: '#ef4444' }} />
          </motion.button>

          {/* Main scanning panel */}
          <motion.div
            initial={{ scale: 0.9, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.9, y: 20 }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="w-full max-w-4xl mx-6 rounded-2xl overflow-hidden"
            style={{
              background: 'rgba(0, 10, 25, 0.85)',
              backdropFilter: 'blur(24px)',
              border: '1px solid rgba(0, 245, 255, 0.3)',
              boxShadow: '0 0 60px rgba(0,245,255,0.15), inset 0 0 60px rgba(0,0,0,0.5)',
            }}
          >
            {/* Header */}
            <div
              className="px-8 py-4 flex items-center justify-between"
              style={{ borderBottom: '1px solid rgba(0,245,255,0.15)' }}
            >
              <div className="flex items-center gap-3">
                <motion.div
                  animate={{ rotate: phase === 'scanning' || phase === 'analyzing' ? 360 : 0 }}
                  transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                >
                  <Scan className="w-5 h-5" style={{ color: '#00f5ff' }} />
                </motion.div>
                <div>
                  <span style={{ ...orb, color: '#00f5ff', fontSize: '14px', letterSpacing: '0.2em' }}>
                    JARVIS SPECTRUM SCANNER
                  </span>
                  <div style={{ ...mono, color: 'rgba(0,245,255,0.5)', fontSize: '10px' }}>
                    FULL SYSTEM ANALYSIS v2.4.1
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <motion.div
                    animate={{ opacity: [1, 0.3, 1] }}
                    transition={{ duration: 0.8, repeat: Infinity }}
                    className="w-2 h-2 rounded-full"
                    style={{ background: phase === 'complete' ? '#22c55e' : '#f59e0b' }}
                  />
                  <span style={{ ...mono, color: phase === 'complete' ? '#22c55e' : '#f59e0b', fontSize: '10px', textTransform: 'uppercase' }}>
                    {phase}
                  </span>
                </div>
                <span style={{ ...orb, color: '#00f5ff', fontSize: '18px' }}>
                  {Math.round(progress)}%
                </span>
              </div>
            </div>

            <div className="flex" style={{ minHeight: 480 }}>
              {/* Left: Scanning visualization */}
              <div
                className="relative overflow-hidden"
                style={{
                  width: '45%',
                  borderRight: '1px solid rgba(0,245,255,0.1)',
                  background: 'rgba(0,5,15,0.4)',
                }}
              >
                {/* Grid overlay */}
                <div
                  className="absolute inset-0"
                  style={{
                    backgroundImage: `
                      linear-gradient(rgba(0,245,255,0.04) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(0,245,255,0.04) 1px, transparent 1px)
                    `,
                    backgroundSize: '30px 30px',
                  }}
                />

                {/* Corner markers */}
                {[
                  { top: 16, left: 16 },
                  { top: 16, right: 16 },
                  { bottom: 16, left: 16 },
                  { bottom: 16, right: 16 },
                ].map((pos, i) => (
                  <div
                    key={i}
                    className="absolute w-6 h-6"
                    style={{
                      ...pos,
                      borderTop: i < 2 ? '2px solid rgba(0,245,255,0.6)' : 'none',
                      borderBottom: i >= 2 ? '2px solid rgba(0,245,255,0.6)' : 'none',
                      borderLeft: i % 2 === 0 ? '2px solid rgba(0,245,255,0.6)' : 'none',
                      borderRight: i % 2 === 1 ? '2px solid rgba(0,245,255,0.6)' : 'none',
                    }}
                  />
                ))}

                {/* Scan beam */}
                <AnimatePresence>
                  {phase === 'scanning' && (
                    <motion.div
                      initial={{ top: 0 }}
                      animate={{ top: '100%' }}
                      transition={{ duration: 3, ease: 'linear', repeat: Infinity }}
                      className="absolute left-0 right-0"
                      style={{
                        height: 3,
                        background: 'linear-gradient(180deg, transparent, rgba(0,245,255,0.8), transparent)',
                        boxShadow: '0 0 20px rgba(0,245,255,0.6), 0 0 40px rgba(0,245,255,0.3)',
                      }}
                    />
                  )}
                </AnimatePresence>

                {/* Data particles */}
                <AnimatePresence>
                  {(phase === 'scanning' || phase === 'analyzing' || phase === 'complete') &&
                    DATA_POINTS.map((pt, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, scale: 0 }}
                        animate={{ opacity: [0, 1, 0.6], scale: 1 }}
                        transition={{ delay: pt.delay, duration: 0.3 }}
                        className="absolute w-1 h-1 rounded-full"
                        style={{
                          left: pt.x,
                          top: pt.y,
                          background: '#00f5ff',
                          boxShadow: '0 0 4px rgba(0,245,255,0.8)',
                        }}
                      />
                    ))}
                </AnimatePresence>

                {/* Center reticle */}
                <div
                  className="absolute"
                  style={{ left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }}
                >
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
                    className="w-24 h-24 rounded-full"
                    style={{ border: '1px solid rgba(0,245,255,0.3)' }}
                  />
                  <motion.div
                    animate={{ rotate: -360 }}
                    transition={{ duration: 6, repeat: Infinity, ease: 'linear' }}
                    className="absolute inset-0 m-auto w-16 h-16 rounded-full"
                    style={{ border: '1px dashed rgba(0,245,255,0.2)' }}
                  />
                  <div
                    className="absolute inset-0 flex items-center justify-center"
                  >
                    {phase === 'complete' ? (
                      <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring' }}>
                        <CheckCircle className="w-8 h-8" style={{ color: '#22c55e' }} />
                      </motion.div>
                    ) : (
                      <Eye className="w-6 h-6" style={{ color: 'rgba(0,245,255,0.7)' }} />
                    )}
                  </div>
                </div>

                {/* Progress bar */}
                <div className="absolute bottom-0 left-0 right-0 p-4">
                  <div className="flex items-center justify-between mb-1.5">
                    <span style={{ ...mono, color: 'rgba(0,245,255,0.6)', fontSize: '9px' }}>SCAN PROGRESS</span>
                    <span style={{ ...mono, color: '#00f5ff', fontSize: '9px' }}>{Math.round(progress)}%</span>
                  </div>
                  <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(0,245,255,0.1)' }}>
                    <motion.div
                      className="h-full rounded-full"
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.3 }}
                      style={{
                        background: 'linear-gradient(90deg, #00f5ff80, #00f5ff)',
                        boxShadow: '0 0 8px rgba(0,245,255,0.6)',
                      }}
                    />
                  </div>
                </div>
              </div>

              {/* Right: Results */}
              <div className="flex-1 p-6 flex flex-col gap-3 overflow-y-auto">
                <div className="flex items-center gap-2 mb-1">
                  <Activity className="w-4 h-4" style={{ color: '#00f5ff' }} />
                  <span style={{ ...orb, color: '#00f5ff', fontSize: '11px', letterSpacing: '0.15em' }}>
                    ANALYSIS RESULTS
                  </span>
                </div>

                {phase !== 'complete' && phase !== 'analyzing' ? (
                  <div className="flex flex-col gap-3">
                    {Array(6).fill(0).map((_, i) => (
                      <motion.div
                        key={i}
                        animate={{ opacity: [0.2, 0.4, 0.2] }}
                        transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.1 }}
                        className="rounded-xl p-3"
                        style={{ background: 'rgba(0,245,255,0.04)', border: '1px solid rgba(0,245,255,0.08)' }}
                      >
                        <div className="h-2 rounded mb-2" style={{ background: 'rgba(0,245,255,0.1)', width: '50%' }} />
                        <div className="h-2 rounded" style={{ background: 'rgba(0,245,255,0.06)', width: '80%' }} />
                      </motion.div>
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col gap-2">
                    {results.slice(0, visibleResults).map((r, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, x: 10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.25 }}
                        className="rounded-xl p-3 flex items-center justify-between"
                        style={{
                          background: 'rgba(0,8,20,0.5)',
                          border: `1px solid ${statusColor[r.status]}20`,
                        }}
                      >
                        <div>
                          <span style={{ ...mono, color: 'rgba(255,255,255,0.4)', fontSize: '9px' }}>{r.category}</span>
                          <p style={{ ...raj, color: 'rgba(255,255,255,0.8)', fontSize: '12px', marginTop: 2 }}>{r.value}</p>
                        </div>
                        <div
                          className="px-2 py-0.5 rounded-lg flex items-center gap-1 flex-shrink-0"
                          style={{
                            background: `${statusColor[r.status]}10`,
                            border: `1px solid ${statusColor[r.status]}30`,
                          }}
                        >
                          <Zap className="w-2.5 h-2.5" style={{ color: statusColor[r.status] }} />
                          <span style={{ ...mono, color: statusColor[r.status], fontSize: '9px', textTransform: 'uppercase' }}>
                            {r.status}
                          </span>
                        </div>
                      </motion.div>
                    ))}
                    {results.length > 0 && visibleResults >= results.length && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="rounded-xl p-4 text-center mt-2"
                        style={{ background: 'rgba(34,197,94,0.06)', border: '1px solid rgba(34,197,94,0.25)' }}
                      >
                        <CheckCircle className="w-5 h-5 mx-auto mb-1.5" style={{ color: '#22c55e' }} />
                        <p style={{ ...orb, color: '#22c55e', fontSize: '11px', letterSpacing: '0.15em' }}>
                          SCAN COMPLETE
                        </p>
                        <p style={{ ...raj, color: 'rgba(34,197,94,0.7)', fontSize: '11px', marginTop: 4 }}>
                          All systems operational. No anomalies detected.
                        </p>
                      </motion.div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
