import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  Globe, Music, FileText, Settings, Brain, Terminal,
  BarChart3, Camera, ChevronUp, Grid
} from 'lucide-react';
import { useApp } from '../context/AppContext';

const orb = { fontFamily: 'Orbitron, sans-serif' };
const mono = { fontFamily: 'Share Tech Mono, monospace' };
const raj = { fontFamily: 'Rajdhani, sans-serif' };

const DOCK_APPS = [
  { id: 'nexus', name: 'JARVIS', icon: Brain, color: '#a855f7' },
  { id: 'terminal', name: 'Terminal', icon: Terminal, color: '#00f5ff' },
  { id: 'browser', name: 'Holoweb', icon: Globe, color: '#0ea5e9' },
  { id: 'monitor', name: 'Monitor', icon: BarChart3, color: '#22c55e' },
  { id: 'vision', name: 'AI Vision', icon: Camera, color: '#ec4899' },
  { id: 'music', name: 'Spotify', icon: Music, color: '#1db954' },
  { id: 'files', name: 'Files', icon: FileText, color: '#f59e0b' },
  { id: 'settings', name: 'Settings', icon: Settings, color: '#64748b' },
];

export function AppDock() {
  const { setAppGridOpen, setSettingsOpen, addNotification } = useApp();
  const [hovered, setHovered] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<string | null>(null);

  const handleClick = (app: typeof DOCK_APPS[0]) => {
    if (app.id === 'settings') {
      setSettingsOpen(true);
    } else {
      addNotification({ type: 'info', title: `${app.name} Launching`, message: `Initializing ${app.name}...` });
    }
  };

  const getScale = (id: string) => {
    if (id === hovered) return 1.4;
    const idx = DOCK_APPS.findIndex(a => a.id === id);
    const hovIdx = DOCK_APPS.findIndex(a => a.id === hovered);
    if (hovered && Math.abs(idx - hovIdx) === 1) return 1.2;
    if (hovered && Math.abs(idx - hovIdx) === 2) return 1.08;
    return 1;
  };

  return (
    <div
      className="fixed bottom-0 left-0 right-0 flex items-center justify-center gap-2 px-4"
      style={{
        height: 72,
        zIndex: 60,
        background: 'rgba(0, 5, 15, 0.85)',
        backdropFilter: 'blur(20px)',
        borderTop: '1px solid rgba(0, 245, 255, 0.1)',
      }}
    >
      {/* Left label */}
      <div className="absolute left-6 flex flex-col">
        <span style={{ ...orb, color: 'rgba(0,245,255,0.5)', fontSize: '8px', letterSpacing: '0.15em' }}>JARVIS</span>
        <span style={{ ...mono, color: 'rgba(0,245,255,0.3)', fontSize: '7px' }}>APP DOCK</span>
      </div>

      {/* Dock inner container */}
      <div
        className="flex items-end gap-1.5 px-4 py-2 rounded-2xl"
        style={{
          background: 'rgba(0, 10, 25, 0.6)',
          border: '1px solid rgba(0,245,255,0.12)',
          boxShadow: '0 0 30px rgba(0,0,0,0.5)',
        }}
      >
        {DOCK_APPS.map(app => (
          <div
            key={app.id}
            className="relative flex flex-col items-center"
            onMouseEnter={() => { setHovered(app.id); setTooltip(app.id); }}
            onMouseLeave={() => { setHovered(null); setTooltip(null); }}
          >
            {/* Tooltip */}
            <AnimatePresence>
              {tooltip === app.id && (
                <motion.div
                  initial={{ opacity: 0, y: 4, scale: 0.9 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 4, scale: 0.9 }}
                  transition={{ duration: 0.15 }}
                  className="absolute bottom-full mb-2 px-2.5 py-1 rounded-lg whitespace-nowrap"
                  style={{
                    background: 'rgba(0,10,25,0.95)',
                    border: `1px solid ${app.color}40`,
                    boxShadow: `0 0 12px ${app.color}20`,
                  }}
                >
                  <span style={{ ...mono, color: app.color, fontSize: '10px' }}>{app.name}</span>
                </motion.div>
              )}
            </AnimatePresence>

            {/* App icon */}
            <motion.button
              onClick={() => handleClick(app)}
              animate={{ scale: getScale(app.id) }}
              transition={{ type: 'spring', stiffness: 400, damping: 25 }}
              className="w-11 h-11 rounded-xl flex items-center justify-center cursor-pointer relative"
              style={{
                background: `radial-gradient(circle, ${app.color}18 0%, rgba(0,0,0,0.5) 100%)`,
                border: `1px solid ${app.color}30`,
                boxShadow: hovered === app.id ? `0 0 16px ${app.color}40` : `0 0 6px ${app.color}10`,
              }}
            >
              <app.icon className="w-5 h-5" style={{ color: app.color }} />

              {/* Active indicator */}
              {(app.id === 'nexus') && (
                <div
                  className="absolute -bottom-1.5 w-1.5 h-1.5 rounded-full"
                  style={{ background: app.color, boxShadow: `0 0 4px ${app.color}` }}
                />
              )}
            </motion.button>
          </div>
        ))}

        {/* Divider */}
        <div className="w-px h-8 mx-1" style={{ background: 'rgba(0,245,255,0.12)' }} />

        {/* App Grid button */}
        <div
          className="relative flex flex-col items-center"
          onMouseEnter={() => setTooltip('grid')}
          onMouseLeave={() => setTooltip(null)}
        >
          <AnimatePresence>
            {tooltip === 'grid' && (
              <motion.div
                initial={{ opacity: 0, y: 4, scale: 0.9 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 4, scale: 0.9 }}
                transition={{ duration: 0.15 }}
                className="absolute bottom-full mb-2 px-2.5 py-1 rounded-lg whitespace-nowrap"
                style={{ background: 'rgba(0,10,25,0.95)', border: '1px solid rgba(0,245,255,0.2)' }}
              >
                <span style={{ ...mono, color: '#00f5ff', fontSize: '10px' }}>All Apps</span>
              </motion.div>
            )}
          </AnimatePresence>
          <motion.button
            whileHover={{ scale: 1.2 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setAppGridOpen(true)}
            className="w-11 h-11 rounded-xl flex items-center justify-center cursor-pointer"
            style={{
              background: 'rgba(0,245,255,0.06)',
              border: '1px solid rgba(0,245,255,0.2)',
            }}
          >
            <Grid className="w-5 h-5" style={{ color: '#00f5ff' }} />
          </motion.button>
        </div>
      </div>

      {/* Right: swipe hint */}
      <div className="absolute right-6 flex items-center gap-1 opacity-50">
        <ChevronUp className="w-3 h-3" style={{ color: 'rgba(0,245,255,0.5)' }} />
        <span style={{ ...mono, color: 'rgba(0,245,255,0.4)', fontSize: '8px' }}>SWIPE UP</span>
      </div>
    </div>
  );
}
