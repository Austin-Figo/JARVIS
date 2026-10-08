import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useApp } from '../context/AppContext';
import { startVoiceRecognition, stopVoiceRecognition } from '../services/jarvisApi';

const orb = { fontFamily: 'Orbitron, sans-serif' };
const mono = { fontFamily: 'Share Tech Mono, monospace' };
const raj = { fontFamily: 'Rajdhani, sans-serif' };

const stateConfig = {
  idle: {
    color: '#00f5ff',
    glow: 'rgba(0, 245, 255, 0.5)',
    label: 'STANDBY',
    subLabel: 'VOICE STANDBY — SAY "HEY JARVIS" OR CLICK TO TALK',
    pulseSpeed: 3,
    ringColor: 'rgba(0,245,255,0.4)',
  },
  listening: {
    color: '#22c55e',
    glow: 'rgba(34, 197, 94, 0.6)',
    label: 'LISTENING',
    subLabel: 'MICROPHONE ACTIVE — SPEAK TO JARVIS NOW',
    pulseSpeed: 0.8,
    ringColor: 'rgba(34,197,94,0.5)',
  },
  processing: {
    color: '#f59e0b',
    glow: 'rgba(245, 158, 11, 0.6)',
    label: 'THINKING',
    subLabel: 'GEMINI NEURAL CORE REASONING',
    pulseSpeed: 0.4,
    ringColor: 'rgba(245,158,11,0.5)',
  },
  responding: {
    color: '#a855f7',
    glow: 'rgba(168, 85, 247, 0.6)',
    label: 'SPEAKING',
    subLabel: 'VOICE SYNTHESIS & RESPONSE ACTIVE',
    pulseSpeed: 0.5,
    ringColor: 'rgba(168,85,247,0.5)',
  },
};

function Ring({
  size,
  thickness,
  color,
  duration,
  direction = 1,
  dashed = false,
  tilt = 0,
}: {
  size: number;
  thickness: number;
  color: string;
  duration: number;
  direction?: number;
  dashed?: boolean;
  tilt?: number;
}) {
  return (
    <motion.div
      animate={{ rotate: direction * 360 }}
      transition={{ duration, repeat: Infinity, ease: 'linear' }}
      className="absolute rounded-full"
      style={{
        width: size,
        height: size,
        left: '50%',
        top: '50%',
        marginLeft: -size / 2,
        marginTop: -size / 2,
        border: `${thickness}px ${dashed ? 'dashed' : 'solid'} ${color}`,
        boxShadow: `0 0 8px ${color.replace('0.', '0.3')}`,
        transform: `rotateX(${tilt}deg)`,
        transformStyle: 'preserve-3d',
      }}
    />
  );
}

export function AICore() {
  const { aiState, setAiState, addNotification, messages } = useApp();
  const cfg = stateConfig[aiState];
  const [dataPoints, setDataPoints] = useState<{ x: number; y: number; val: string }[]>([]);

  // Find the latest AI reply and user question
  const latestAiMsg = [...messages].reverse().find(m => m.type === 'ai');
  const latestUserMsg = [...messages].reverse().find(m => m.type === 'user');

  useEffect(() => {
    const pts = Array(8).fill(0).map((_, i) => {
      const angle = (i / 8) * Math.PI * 2;
      const r = 150;
      return {
        x: Math.cos(angle) * r,
        y: Math.sin(angle) * r,
        val: `${(Math.random() * 100).toFixed(1)}%`,
      };
    });
    setDataPoints(pts);
    const interval = setInterval(() => {
      setDataPoints(prev =>
        prev.map(p => ({ ...p, val: `${(Math.random() * 100).toFixed(1)}%` }))
      );
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleClick = async () => {
    if (aiState === 'listening') {
      try {
        await stopVoiceRecognition();
        setAiState('idle');
        addNotification({ type: 'info', title: 'Voice Standby', message: 'Microphone on standby. Say "Hey Jarvis" or click to speak.' });
      } catch {
        setAiState('idle');
      }
    } else {
      try {
        const res = await startVoiceRecognition();
        if (res.ok) {
          setAiState('listening');
          addNotification({ type: 'success', title: 'Listening Active', message: 'Microphone listening! Speak to JARVIS now.' });
        }
      } catch {
        addNotification({ type: 'error', title: 'Voice', message: 'Microphone currently unavailable.' });
      }
    }
  };

  return (
    <div className="flex flex-col items-center justify-center gap-6 select-none" style={{ perspective: '600px' }}>
      {/* Outer data ring indicators */}
      <div className="relative" style={{ width: 380, height: 380 }}>
        {/* Data point markers */}
        {dataPoints.map((pt, i) => (
          <motion.div
            key={i}
            animate={{ opacity: [0.4, 1, 0.4] }}
            transition={{ duration: 2 + i * 0.3, repeat: Infinity, delay: i * 0.25 }}
            className="absolute flex items-center gap-1"
            style={{
              left: '50%',
              top: '50%',
              transform: `translate(${pt.x - 20}px, ${pt.y - 10}px)`,
            }}
          >
            <div className="w-1.5 h-1.5 rounded-full" style={{ background: cfg.color, boxShadow: `0 0 4px ${cfg.color}` }} />
            <span style={{ ...mono, color: cfg.color, fontSize: '9px', opacity: 0.7 }}>{pt.val}</span>
          </motion.div>
        ))}

        {/* Outer dashed ring */}
        <Ring size={340} thickness={1} color="rgba(0,245,255,0.1)" duration={40} dashed />

        {/* Ring 1 — large slow */}
        <Ring size={300} thickness={1} color={cfg.ringColor.replace('0.5', '0.2')} duration={20} direction={1} tilt={20} />
        {/* Ring 2 — medium counter */}
        <Ring size={260} thickness={1.5} color={cfg.ringColor.replace('0.5', '0.3')} duration={14} direction={-1} tilt={-15} />
        {/* Ring 3 — fast accent */}
        <Ring size={210} thickness={1} color={cfg.ringColor} duration={8} direction={1} />

        {/* Pulse wave rings */}
        <motion.div
          animate={{ scale: [1, 1.4, 1], opacity: [0.3, 0, 0.3] }}
          transition={{ duration: cfg.pulseSpeed * 2, repeat: Infinity }}
          className="absolute rounded-full"
          style={{
            width: 180,
            height: 180,
            left: '50%',
            top: '50%',
            marginLeft: -90,
            marginTop: -90,
            border: `1px solid ${cfg.color}`,
          }}
        />
        <motion.div
          animate={{ scale: [1, 1.6, 1], opacity: [0.2, 0, 0.2] }}
          transition={{ duration: cfg.pulseSpeed * 2, repeat: Infinity, delay: 0.4 }}
          className="absolute rounded-full"
          style={{
            width: 180,
            height: 180,
            left: '50%',
            top: '50%',
            marginLeft: -90,
            marginTop: -90,
            border: `1px solid ${cfg.color}`,
          }}
        />

        {/* Clickable Core Orb */}
        <motion.div
          onClick={handleClick}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="absolute cursor-pointer rounded-full flex items-center justify-center"
          style={{
            width: 160,
            height: 160,
            left: '50%',
            top: '50%',
            marginLeft: -80,
            marginTop: -80,
            background: `radial-gradient(circle at 35% 35%, ${cfg.color}25 0%, rgba(0,5,20,0.9) 60%, rgba(0,2,10,1) 100%)`,
            border: `2px solid ${cfg.color}`,
            boxShadow: `0 0 30px ${cfg.glow}, 0 0 60px ${cfg.glow.replace('0.5', '0.2')}, inset 0 0 30px ${cfg.glow.replace('0.5', '0.15')}`,
            transition: 'box-shadow 0.5s, border-color 0.5s, background 0.5s',
          }}
        >
          {/* Inner glow core */}
          <motion.div
            animate={{ scale: [1, 1.15, 1], opacity: [0.8, 1, 0.8] }}
            transition={{ duration: cfg.pulseSpeed, repeat: Infinity }}
            className="rounded-full flex items-center justify-center flex-col gap-1"
            style={{
              width: 120,
              height: 120,
              background: `radial-gradient(circle, ${cfg.color}20 0%, transparent 70%)`,
            }}
          >
            {/* Core logo */}
            <motion.div
              animate={{ rotate: aiState === 'processing' ? 360 : 0 }}
              transition={{ duration: 1.5, repeat: aiState === 'processing' ? Infinity : 0, ease: 'linear' }}
            >
              <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                <circle cx="18" cy="18" r="16" stroke={cfg.color} strokeWidth="1" opacity="0.5" />
                <circle cx="18" cy="18" r="10" stroke={cfg.color} strokeWidth="1.5" opacity="0.8" />
                <circle cx="18" cy="18" r="4" fill={cfg.color} />
                <line x1="18" y1="2" x2="18" y2="8" stroke={cfg.color} strokeWidth="1.5" />
                <line x1="18" y1="28" x2="18" y2="34" stroke={cfg.color} strokeWidth="1.5" />
                <line x1="2" y1="18" x2="8" y2="18" stroke={cfg.color} strokeWidth="1.5" />
                <line x1="28" y1="18" x2="34" y2="18" stroke={cfg.color} strokeWidth="1.5" />
              </svg>
            </motion.div>
            <span style={{ ...orb, color: cfg.color, fontSize: '8px', letterSpacing: '0.1em', textAlign: 'center', opacity: 0.9 }}>
              JARVIS
            </span>
          </motion.div>
        </motion.div>
      </div>

      {/* State label */}
      <div className="flex flex-col items-center gap-2">
        <AnimatePresence mode="wait">
          <motion.div
            key={aiState}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.3 }}
            className="flex flex-col items-center gap-1"
          >
            <span
              style={{
                ...orb,
                color: cfg.color,
                fontSize: '16px',
                letterSpacing: '0.25em',
                textShadow: `0 0 15px ${cfg.glow}`,
              }}
            >
              {cfg.label}
            </span>
            <span style={{ ...mono, color: 'rgba(255,255,255,0.35)', fontSize: '10px', letterSpacing: '0.12em' }}>
              {cfg.subLabel}
            </span>
          </motion.div>
        </AnimatePresence>

        {/* Status bar */}
        <div className="flex items-center gap-3 mt-1">
          {['NEURAL', 'VOICE', 'MEMORY', 'NETWORK'].map((item, i) => (
            <div key={item} className="flex flex-col items-center gap-1">
              <div
                className="w-12 h-0.5 rounded-full overflow-hidden"
                style={{ background: 'rgba(255,255,255,0.06)' }}
              >
                <motion.div
                  className="h-full rounded-full"
                  animate={{ width: [`${50 + i * 10}%`, `${70 + i * 5}%`, `${50 + i * 10}%`] }}
                  transition={{ duration: 3 + i * 0.5, repeat: Infinity }}
                  style={{ background: cfg.color, boxShadow: `0 0 4px ${cfg.color}` }}
                />
              </div>
              <span style={{ ...mono, color: 'rgba(255,255,255,0.25)', fontSize: '8px' }}>{item}</span>
            </div>
          ))}
        </div>

        {/* Dynamic Holographic Speech / Response Bubble */}
        <AnimatePresence>
          {latestAiMsg && (
            <motion.div
              key={latestAiMsg.id}
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 5 }}
              transition={{ duration: 0.3 }}
              className="max-w-lg text-center px-5 py-3 rounded-2xl flex flex-col items-center gap-1.5"
              style={{
                background: 'rgba(0, 10, 28, 0.85)',
                border: `1px solid ${cfg.color}35`,
                boxShadow: `0 0 25px ${cfg.color}20`,
                backdropFilter: 'blur(16px)',
              }}
            >
              {latestUserMsg && (
                <span style={{ ...mono, color: 'rgba(0, 245, 255, 0.6)', fontSize: '10px' }}>
                  YOU: "{latestUserMsg.text}"
                </span>
              )}
              <p style={{ ...raj, color: '#ffffff', fontSize: '13px', lineHeight: '1.4', fontWeight: 500 }}>
                {latestAiMsg.text}
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Click hint */}
        <motion.p
          animate={{ opacity: [0.35, 0.85, 0.35] }}
          transition={{ duration: 2.2, repeat: Infinity }}
          style={{ ...raj, color: cfg.color, fontSize: '12px', marginTop: 4, letterSpacing: '0.08em' }}
        >
          {aiState === 'listening' ? '● MICROPHONE LISTENING — CLICK TO PAUSE' : 'CLICK ORB OR SAY "HEY JARVIS" TO TALK'}
        </motion.p>
      </div>
    </div>
  );
}
