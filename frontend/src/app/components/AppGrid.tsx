import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  X, Globe, Music, FileText, Settings, Cpu, Brain, Camera, Terminal,
  BarChart3, Lock, Cloud, Wifi, Zap, Map, Code, Video, Mail, Phone,
  Calendar, Clock, Package, Database, Shield, Star
} from 'lucide-react';
import { useApp } from '../context/AppContext';

const orb = { fontFamily: 'Orbitron, sans-serif' };
const mono = { fontFamily: 'Share Tech Mono, monospace' };
const raj = { fontFamily: 'Rajdhani, sans-serif' };

const APPS = [
  // System
  { id: 'terminal', name: 'Terminal', icon: Terminal, color: '#00f5ff', cat: 'System' },
  { id: 'settings', name: 'Settings', icon: Settings, color: '#0ea5e9', cat: 'System' },
  { id: 'monitor', name: 'Monitor', icon: Cpu, color: '#22c55e', cat: 'System' },
  { id: 'security', name: 'Security', icon: Shield, color: '#ef4444', cat: 'System' },
  { id: 'storage', name: 'Storage', icon: Database, color: '#f59e0b', cat: 'System' },
  { id: 'network', name: 'Network', icon: Wifi, color: '#8b5cf6', cat: 'System' },
  // AI
  { id: 'nexus', name: 'JARVIS Core', icon: Brain, color: '#a855f7', cat: 'AI' },
  { id: 'vision', name: 'AI Vision', icon: Camera, color: '#ec4899', cat: 'AI' },
  { id: 'analyze', name: 'Analyzer', icon: BarChart3, color: '#06b6d4', cat: 'AI' },
  { id: 'code', name: 'Code AI', icon: Code, color: '#10b981', cat: 'AI' },
  { id: 'memory', name: 'Memory', icon: Package, color: '#f97316', cat: 'AI' },
  { id: 'encrypt', name: 'Vault', icon: Lock, color: '#6366f1', cat: 'AI' },
  // Media
  { id: 'browser', name: 'Holoweb', icon: Globe, color: '#0ea5e9', cat: 'Media' },
  { id: 'music', name: 'Spotify', icon: Music, color: '#22c55e', cat: 'Media' },
  { id: 'video', name: 'HoloVid', icon: Video, color: '#f59e0b', cat: 'Media' },
  { id: 'maps', name: 'NexMap', icon: Map, color: '#06b6d4', cat: 'Media' },
  // Comms
  { id: 'mail', name: 'Mail', icon: Mail, color: '#a855f7', cat: 'Comms' },
  { id: 'call', name: 'Comms', icon: Phone, color: '#22c55e', cat: 'Comms' },
  { id: 'cloud', name: 'Cloud Sync', icon: Cloud, color: '#0ea5e9', cat: 'Comms' },
  { id: 'files', name: 'Files', icon: FileText, color: '#f59e0b', cat: 'Comms' },
  // More
  { id: 'calendar', name: 'Calendar', icon: Calendar, color: '#ec4899', cat: 'Tools' },
  { id: 'clock', name: 'ChronOS', icon: Clock, color: '#8b5cf6', cat: 'Tools' },
  { id: 'power', name: 'Power AI', icon: Zap, color: '#f97316', cat: 'Tools' },
  { id: 'starred', name: 'Favorites', icon: Star, color: '#eab308', cat: 'Tools' },
];

const CATEGORIES = ['All', 'System', 'AI', 'Media', 'Comms', 'Tools'];

export function AppGrid() {
  const { appGridOpen, setAppGridOpen, setSettingsOpen, addNotification } = useApp();
  const [activeCategory, setActiveCategory] = useState('All');
  const [hoveredApp, setHoveredApp] = useState<string | null>(null);

  const filtered = APPS.filter(a => activeCategory === 'All' || a.cat === activeCategory);

  const handleAppClick = (app: typeof APPS[0]) => {
    if (app.id === 'settings') {
      setSettingsOpen(true);
      setAppGridOpen(false);
    } else {
      addNotification({ type: 'info', title: `${app.name} Launched`, message: `${app.name} is initializing...` });
      setAppGridOpen(false);
    }
  };

  return (
    <AnimatePresence>
      {appGridOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.25 }}
          className="fixed inset-0 flex flex-col"
          style={{ zIndex: 150, background: 'rgba(0, 4, 12, 0.95)', backdropFilter: 'blur(20px)' }}
        >
          {/* Header */}
          <div
            className="flex items-center justify-between px-10 py-5 flex-shrink-0"
            style={{ borderBottom: '1px solid rgba(0,245,255,0.1)' }}
          >
            <div>
              <h2 style={{ ...orb, color: '#00f5ff', fontSize: '18px', letterSpacing: '0.2em', margin: 0, textShadow: '0 0 20px rgba(0,245,255,0.5)' }}>
                APP LAUNCHER
              </h2>
              <p style={{ ...mono, color: 'rgba(0,245,255,0.4)', fontSize: '10px', marginTop: 4 }}>
                {APPS.length} APPLICATIONS AVAILABLE
              </p>
            </div>
            <motion.button
              whileHover={{ scale: 1.1, rotate: 90 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => setAppGridOpen(false)}
              className="w-10 h-10 rounded-xl flex items-center justify-center cursor-pointer"
              style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)' }}
            >
              <X className="w-5 h-5" style={{ color: '#ef4444' }} />
            </motion.button>
          </div>

          {/* Category tabs */}
          <div className="flex gap-2 px-10 py-4 flex-shrink-0">
            {CATEGORIES.map(cat => (
              <motion.button
                key={cat}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setActiveCategory(cat)}
                className="px-4 py-2 rounded-xl cursor-pointer"
                style={{
                  background: activeCategory === cat ? 'rgba(0,245,255,0.12)' : 'rgba(0,245,255,0.03)',
                  border: `1px solid ${activeCategory === cat ? 'rgba(0,245,255,0.4)' : 'rgba(0,245,255,0.1)'}`,
                  boxShadow: activeCategory === cat ? '0 0 12px rgba(0,245,255,0.1)' : 'none',
                }}
              >
                <span style={{ ...mono, color: activeCategory === cat ? '#00f5ff' : 'rgba(0,245,255,0.4)', fontSize: '11px' }}>
                  {cat.toUpperCase()}
                </span>
              </motion.button>
            ))}
          </div>

          {/* App grid */}
          <div className="flex-1 overflow-y-auto px-10 pb-10">
            <motion.div
              layout
              className="grid gap-4"
              style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))' }}
            >
              <AnimatePresence mode="popLayout">
                {filtered.map((app, i) => (
                  <motion.div
                    key={app.id}
                    layout
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    transition={{ duration: 0.2, delay: i * 0.03 }}
                    whileHover={{ scale: 1.08, y: -4 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => handleAppClick(app)}
                    onMouseEnter={() => setHoveredApp(app.id)}
                    onMouseLeave={() => setHoveredApp(null)}
                    className="flex flex-col items-center gap-3 p-4 rounded-2xl cursor-pointer"
                    style={{
                      background: hoveredApp === app.id
                        ? `rgba(${hexToRgb(app.color)}, 0.08)`
                        : 'rgba(255,255,255,0.02)',
                      border: `1px solid ${hoveredApp === app.id
                        ? `${app.color}40`
                        : 'rgba(255,255,255,0.06)'}`,
                      boxShadow: hoveredApp === app.id
                        ? `0 0 20px ${app.color}15, inset 0 0 20px rgba(0,0,0,0.3)`
                        : 'none',
                      transition: 'all 0.2s',
                    }}
                  >
                    {/* App icon */}
                    <div
                      className="w-14 h-14 rounded-2xl flex items-center justify-center relative"
                      style={{
                        background: `radial-gradient(circle, ${app.color}20 0%, rgba(0,0,0,0.5) 100%)`,
                        border: `1px solid ${app.color}30`,
                        boxShadow: hoveredApp === app.id ? `0 0 20px ${app.color}30` : `0 0 8px ${app.color}10`,
                      }}
                    >
                      <app.icon className="w-7 h-7" style={{ color: app.color }} />
                    </div>

                    {/* App name */}
                    <span
                      style={{
                        ...raj,
                        color: hoveredApp === app.id ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.6)',
                        fontSize: '12px',
                        textAlign: 'center',
                        lineHeight: 1.2,
                        transition: 'color 0.2s',
                      }}
                    >
                      {app.name}
                    </span>
                  </motion.div>
                ))}
              </AnimatePresence>
            </motion.div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function hexToRgb(hex: string): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `${r}, ${g}, ${b}`;
}
