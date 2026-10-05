import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Brain, Terminal, Search, Activity } from 'lucide-react';

import { AppProvider, useApp } from './context/AppContext';
import { Background } from './components/Background';
import { TopBar } from './components/TopBar';
import { AICore } from './components/AICore';
import { SystemMonitor } from './components/SystemMonitor';
import { MemoryPanel } from './components/MemoryPanel';
import { CommandConsole } from './components/CommandConsole';
import { SearchPanel } from './components/SearchPanel';
import { VoiceBar } from './components/VoiceBar';
import { ScanningPanel } from './components/ScanningPanel';
import { AppGrid } from './components/AppGrid';
import { AppDock } from './components/AppDock';
import { SettingsPanel } from './components/SettingsPanel';
import { GesturePanel } from './components/GesturePanel';
import { NotificationSystem } from './components/NotificationSystem';
import { ConfirmationDialog } from './components/ConfirmationDialog';

const orb = { fontFamily: 'Orbitron, sans-serif' };
const mono = { fontFamily: 'Share Tech Mono, monospace' };
const raj = { fontFamily: 'Rajdhani, sans-serif' };

const glassPanel = (accent = '#00f5ff') => ({
  background: 'rgba(0, 10, 28, 0.65)',
  backdropFilter: 'blur(20px)',
  border: `1px solid ${accent}20`,
  borderRadius: '16px',
  boxShadow: `0 0 30px rgba(0,0,0,0.4), inset 0 0 20px rgba(0,0,0,0.3)`,
});

function PanelTab({
  id, label, icon: Icon, active, color, onClick,
}: {
  id: string; label: string; icon: React.ElementType;
  active: boolean; color: string; onClick: () => void;
}) {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className="flex items-center gap-2 px-3 py-2 rounded-xl cursor-pointer"
      style={{
        background: active ? `${color}12` : 'rgba(255,255,255,0.02)',
        border: `1px solid ${active ? `${color}35` : 'rgba(255,255,255,0.06)'}`,
        transition: 'all 0.2s',
      }}
    >
      <Icon className="w-3.5 h-3.5" style={{ color: active ? color : 'rgba(255,255,255,0.3)' }} />
      <span style={{ ...mono, color: active ? color : 'rgba(255,255,255,0.35)', fontSize: '9px', letterSpacing: '0.08em' }}>
        {label}
      </span>
    </motion.button>
  );
}

function MainLayout() {
  const { leftPanel, setLeftPanel, rightPanel, setRightPanel } = useApp();

  return (
    <div
      className="fixed inset-0 flex flex-col overflow-hidden"
      style={{ fontFamily: 'Rajdhani, sans-serif' }}
    >
      <Background />

      {/* Top Bar */}
      <TopBar />

      {/* Main 3-column layout */}
      <div
        className="flex flex-1 gap-4 px-4 overflow-hidden"
        style={{ marginTop: 56, marginBottom: 144 }}
      >
        {/* LEFT PANEL */}
        <div
          className="w-72 flex-shrink-0 flex flex-col gap-3 overflow-hidden pt-4 pb-2"
        >
          {/* Panel tabs */}
          <div className="flex gap-2 flex-shrink-0">
            <PanelTab
              id="monitor" label="MONITOR" icon={Activity}
              active={leftPanel === 'monitor'} color="#00f5ff"
              onClick={() => setLeftPanel('monitor')}
            />
            <PanelTab
              id="memory" label="MEMORY" icon={Brain}
              active={leftPanel === 'memory'} color="#a855f7"
              onClick={() => setLeftPanel('memory')}
            />
          </div>

          {/* Panel content */}
          <div
            className="flex-1 p-4 overflow-hidden"
            style={glassPanel(leftPanel === 'monitor' ? '#00f5ff' : '#a855f7')}
          >
            <AnimatePresence mode="wait">
              {leftPanel === 'monitor' ? (
                <motion.div key="monitor" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
                  <SystemMonitor />
                </motion.div>
              ) : (
                <motion.div key="memory" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
                  <MemoryPanel />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* CENTER — AI Core */}
        <div className="flex-1 flex flex-col items-center justify-center gap-4 overflow-hidden">
          {/* Top data strip */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-md flex items-center justify-between px-6 py-2.5 rounded-xl flex-shrink-0"
            style={{
              background: 'rgba(0,8,22,0.5)',
              border: '1px solid rgba(0,245,255,0.1)',
              backdropFilter: 'blur(12px)',
            }}
          >
            {[
              { label: 'NEURAL OPS', value: '1.2T', color: '#00f5ff' },
              { label: 'CONTEXT', value: '128K', color: '#a855f7' },
              { label: 'ACCURACY', value: '98.7%', color: '#22c55e' },
              { label: 'LATENCY', value: '42ms', color: '#f59e0b' },
            ].map(({ label, value, color }) => (
              <div key={label} className="flex flex-col items-center">
                <span style={{ ...orb, color, fontSize: '13px', textShadow: `0 0 8px ${color}` }}>{value}</span>
                <span style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '8px' }}>{label}</span>
              </div>
            ))}
          </motion.div>

          {/* AI Core orb */}
          <div className="flex-1 flex items-center justify-center w-full">
            <AICore />
          </div>

          {/* Bottom info strip */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-sm flex flex-col gap-2 flex-shrink-0"
          >
            {/* Quick action buttons */}
            <div className="flex items-center justify-center gap-3">
              {[
                { label: 'SCAN', color: '#00f5ff', action: 'scan' },
                { label: 'ANALYZE', color: '#a855f7', action: 'analyze' },
                { label: 'DEPLOY', color: '#22c55e', action: 'deploy' },
                { label: 'SECURE', color: '#f59e0b', action: 'encrypt' },
              ].map(({ label, color, action }) => (
                <QuickActionButton key={label} label={label} color={color} action={action} />
              ))}
            </div>
          </motion.div>
        </div>

        {/* RIGHT PANEL */}
        <div className="w-72 flex-shrink-0 flex flex-col gap-3 overflow-hidden pt-4 pb-2">
          {/* Panel tabs */}
          <div className="flex gap-2 flex-shrink-0">
            <PanelTab
              id="console" label="CONSOLE" icon={Terminal}
              active={rightPanel === 'console'} color="#00f5ff"
              onClick={() => setRightPanel('console')}
            />
            <PanelTab
              id="search" label="SEARCH" icon={Search}
              active={rightPanel === 'search'} color="#0ea5e9"
              onClick={() => setRightPanel('search')}
            />
          </div>

          {/* Panel content */}
          <div
            className="flex-1 p-4 overflow-hidden"
            style={glassPanel(rightPanel === 'console' ? '#00f5ff' : '#0ea5e9')}
          >
            <AnimatePresence mode="wait">
              {rightPanel === 'console' ? (
                <motion.div key="console" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
                  <CommandConsole />
                </motion.div>
              ) : (
                <motion.div key="search" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
                  <SearchPanel />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* Voice Bar */}
      <VoiceBar />

      {/* App Dock */}
      <AppDock />

      {/* Overlays */}
      <ScanningPanel />
      <AppGrid />
      <SettingsPanel />
      <GesturePanel />

      {/* Notifications */}
      <NotificationSystem />
      <ConfirmationDialog />
    </div>
  );
}

function QuickActionButton({ label, color, action }: { label: string; color: string; action: string }) {
  const { addMessage, setAiState, setScanningActive, addNotification } = useApp();

  const handleClick = () => {
    addMessage({ type: 'user', text: action });
    setAiState('processing');
    if (action === 'scan') {
      setTimeout(() => {
        setScanningActive(true);
        setAiState('responding');
        addMessage({ type: 'ai', text: 'Scan initiated. Holographic display activating...' });
        setTimeout(() => setAiState('idle'), 2000);
      }, 600);
    } else {
      setTimeout(() => {
        setAiState('responding');
        const resp = action === 'analyze'
          ? 'Deep neural analysis running... Pattern recognition: 99.2% confidence. No anomalies found.'
          : action === 'deploy'
          ? 'Deployment initiated. Docker container built. Production deployment: successful. Zero downtime.'
          : 'Encryption protocol activated. AES-256 + RSA-4096 engaged. All channels secured.';
        addMessage({ type: 'ai', text: resp });
        addNotification({ type: 'success', title: `${label} Complete`, message: resp.slice(0, 60) + '...' });
        setTimeout(() => setAiState('idle'), 2000);
      }, 1000);
    }
  };

  return (
    <motion.button
      whileHover={{ scale: 1.05, y: -2 }}
      whileTap={{ scale: 0.95 }}
      onClick={handleClick}
      className="px-4 py-2 rounded-xl cursor-pointer"
      style={{
        background: `${color}0a`,
        border: `1px solid ${color}30`,
        transition: 'box-shadow 0.2s',
      }}
      onMouseEnter={e => (e.currentTarget as HTMLElement).style.boxShadow = `0 0 16px ${color}25`}
      onMouseLeave={e => (e.currentTarget as HTMLElement).style.boxShadow = 'none'}
    >
      <span style={{ ...mono, color, fontSize: '10px', letterSpacing: '0.08em' }}>{label}</span>
    </motion.button>
  );
}

export default function App() {
  return (
    <AppProvider>
      <MainLayout />
    </AppProvider>
  );
}
