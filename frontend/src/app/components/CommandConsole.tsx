import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Terminal, Send, Trash2, Download } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { sendCommand } from '../services/jarvisApi';

const orb = { fontFamily: 'Orbitron, sans-serif' };
const mono = { fontFamily: 'Share Tech Mono, monospace' };
const raj = { fontFamily: 'Rajdhani, sans-serif' };

const AI_RESPONSES: Record<string, string> = {
  scan: 'Initiating full-spectrum environmental scan. Holographic display activating...',
  status: 'All systems nominal. CPU: 42% | Memory: 62% | Network: Online | Security: AES-256 Active | Uptime: 4h 12m.',
  time: `Current time: ${new Date().toLocaleTimeString()}. Temporal reference synchronized with UTC+0.`,
  hello: 'Hello! JARVIS is fully operational and ready to assist. All neural pathways active.',
  help: 'Available commands: scan, status, time, hello, settings, apps, gesture, weather, memory, encrypt. Say or type any command.',
  settings: 'Opening system configuration panel. Initializing secure environment...',
  apps: 'Launching application grid interface. Holographic display ready.',
  gesture: 'Activating gesture recognition module. Camera feed initializing...',
  weather: 'Fetching atmospheric data... Conditions: Clear skies, 22°C, Humidity: 58%, Wind: 12 km/h NE. Air quality: Good.',
  memory: 'Memory core accessed. 5 records found. Local: Synced | Cloud: Active | Git: Pushed.',
  encrypt: 'Running encryption protocol... AES-256 verified. RSA-4096 key exchange complete. All channels secure.',
  deploy: 'Initiating deployment sequence. Building Docker container... Pushing to registry... Deployed to production. Zero downtime achieved.',
  analyze: 'Running deep neural analysis... Pattern recognition active... Anomaly detection: None found. Confidence: 98.7%.',
  shutdown: 'Shutdown sequence initiated. Saving session state... Encrypting memory... Graceful shutdown in 30 seconds. Say "cancel" to abort.',
  cancel: 'Shutdown sequence aborted. All systems remain active. Standing by for further commands.',
};

const SUGGESTIONS = ['scan', 'status', 'weather', 'deploy', 'analyze', 'help'];

function TypingText({ text, onDone }: { text: string; onDone?: () => void }) {
  const [displayed, setDisplayed] = useState('');
  const [done, setDone] = useState(false);

  useEffect(() => {
    setDisplayed('');
    setDone(false);
    let i = 0;
    const speed = Math.max(15, 35 - text.length * 0.1);
    const interval = setInterval(() => {
      if (i < text.length) {
        setDisplayed(text.slice(0, i + 1));
        i++;
      } else {
        setDone(true);
        clearInterval(interval);
        onDone?.();
      }
    }, speed);
    return () => clearInterval(interval);
  }, [text]);

  return (
    <span>
      {displayed}
      {!done && (
        <motion.span
          animate={{ opacity: [1, 0] }}
          transition={{ duration: 0.5, repeat: Infinity }}
          style={{ color: '#00f5ff' }}
        >
          ▋
        </motion.span>
      )}
    </span>
  );
}

export function CommandConsole() {
  const { messages, addMessage, setAiState, setScanningActive, setSettingsOpen, setAppGridOpen, setGestureOpen, addNotification, setPendingConfirmation } = useApp();
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSubmit = async () => {
    if (!input.trim() || isTyping) return;
    const text = input.trim();
    setInput('');

    addMessage({ type: 'user', text });
    setAiState('processing');
    setIsTyping(true);

    try {
      const response = await sendCommand(text);
      setAiState('responding');
      addMessage({ type: 'ai', text: response.message });
      if (response.requires_confirmation && response.confirmation) {
        setPendingConfirmation({ ...response.confirmation, source: 'console' });
        addNotification({ type: 'warning', title: 'Confirmation Required', message: response.confirmation.message });
      }
      if (response.action === 'scan') setScanningActive(true);
      if (response.action === 'settings') setSettingsOpen(true);
      if (response.action === 'apps') setAppGridOpen(true);
      if (response.action === 'gesture') setGestureOpen(true);
      addNotification({ type: 'info', title: 'JARVIS Response', message: response.message });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to reach the JARVIS service.';
      addMessage({ type: 'ai', text: message });
      addNotification({ type: 'error', title: 'Backend Offline', message });
    } finally {
      setIsTyping(false);
      setTimeout(() => setAiState('idle'), 600);
    }
  };

  return (
    <div className="flex flex-col h-full gap-3 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4" style={{ color: '#00f5ff' }} />
          <span style={{ ...orb, color: '#00f5ff', fontSize: '11px', letterSpacing: '0.15em' }}>
            COMMAND CONSOLE
          </span>
        </div>
        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            className="p-1.5 rounded-lg cursor-pointer"
            style={{ background: 'rgba(0,245,255,0.05)', border: '1px solid rgba(0,245,255,0.12)' }}
          >
            <Download className="w-3 h-3" style={{ color: 'rgba(0,245,255,0.5)' }} />
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            className="p-1.5 rounded-lg cursor-pointer"
            style={{ background: 'rgba(0,245,255,0.05)', border: '1px solid rgba(0,245,255,0.12)' }}
          >
            <Trash2 className="w-3 h-3" style={{ color: 'rgba(0,245,255,0.5)' }} />
          </motion.button>
        </div>
      </div>

      {/* Messages */}
      <div
        className="flex-1 overflow-y-auto flex flex-col gap-3 pr-1"
        style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(0,245,255,0.2) transparent' }}
      >
        <AnimatePresence initial={false}>
          {messages.map(msg => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.25 }}
              className={`flex gap-2 ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.type === 'ai' && (
                <div
                  className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                  style={{
                    background: 'rgba(0,245,255,0.1)',
                    border: '1px solid rgba(0,245,255,0.3)',
                    boxShadow: '0 0 8px rgba(0,245,255,0.2)',
                  }}
                >
                  <div className="w-1.5 h-1.5 rounded-full" style={{ background: '#00f5ff' }} />
                </div>
              )}

              <div
                className="max-w-[85%] rounded-2xl px-3.5 py-2.5"
                style={
                  msg.type === 'ai'
                    ? {
                        background: 'rgba(0, 245, 255, 0.05)',
                        border: '1px solid rgba(0,245,255,0.2)',
                        boxShadow: '0 0 12px rgba(0,245,255,0.05)',
                        borderRadius: '4px 16px 16px 16px',
                      }
                    : {
                        background: 'rgba(168, 85, 247, 0.12)',
                        border: '1px solid rgba(168,85,247,0.3)',
                        boxShadow: '0 0 12px rgba(168,85,247,0.08)',
                        borderRadius: '16px 4px 16px 16px',
                      }
                }
              >
                {msg.type === 'ai' ? (
                  <p style={{ ...raj, color: 'rgba(220,240,255,0.9)', fontSize: '13px', lineHeight: '1.6' }}>
                    <TypingText text={msg.text} />
                  </p>
                ) : (
                  <p style={{ ...raj, color: 'rgba(220,200,255,0.9)', fontSize: '13px', lineHeight: '1.6' }}>
                    {msg.text}
                  </p>
                )}
                <div className="mt-1 flex justify-end">
                  <span style={{ ...mono, color: 'rgba(255,255,255,0.2)', fontSize: '9px' }}>
                    {msg.timestamp.toLocaleTimeString('en-US', { hour12: false })}
                  </span>
                </div>
              </div>

              {msg.type === 'user' && (
                <div
                  className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                  style={{
                    background: 'rgba(168,85,247,0.15)',
                    border: '1px solid rgba(168,85,247,0.4)',
                    boxShadow: '0 0 8px rgba(168,85,247,0.2)',
                  }}
                >
                  <div className="w-1.5 h-1.5 rounded-full" style={{ background: '#a855f7' }} />
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Typing indicator */}
        <AnimatePresence>
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              className="flex gap-2 items-center"
            >
              <div
                className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0"
                style={{ background: 'rgba(0,245,255,0.1)', border: '1px solid rgba(0,245,255,0.3)' }}
              >
                <div className="w-1.5 h-1.5 rounded-full" style={{ background: '#00f5ff' }} />
              </div>
              <div
                className="px-3 py-2 rounded-2xl flex items-center gap-1.5"
                style={{ background: 'rgba(0,245,255,0.05)', border: '1px solid rgba(0,245,255,0.15)' }}
              >
                {[0, 1, 2].map(i => (
                  <motion.div
                    key={i}
                    animate={{ y: [-2, 2, -2] }}
                    transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.15 }}
                    className="w-1.5 h-1.5 rounded-full"
                    style={{ background: '#00f5ff' }}
                  />
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={endRef} />
      </div>

      {/* Suggestions */}
      <div className="flex flex-wrap gap-1.5 flex-shrink-0">
        {SUGGESTIONS.map(s => (
          <motion.button
            key={s}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => { setInput(s); inputRef.current?.focus(); }}
            className="px-2.5 py-1 rounded-lg cursor-pointer"
            style={{
              background: 'rgba(0,245,255,0.04)',
              border: '1px solid rgba(0,245,255,0.15)',
            }}
          >
            <span style={{ ...mono, color: 'rgba(0,245,255,0.6)', fontSize: '9px' }}>{s}</span>
          </motion.button>
        ))}
      </div>

      {/* Input */}
      <div
        className="flex items-center gap-2 rounded-xl px-3 py-2.5 flex-shrink-0"
        style={{
          background: 'rgba(0,8,25,0.7)',
          border: '1px solid rgba(0,245,255,0.2)',
          boxShadow: '0 0 10px rgba(0,245,255,0.04)',
        }}
      >
        <span style={{ ...mono, color: 'rgba(0,245,255,0.5)', fontSize: '12px' }}>{'>'}</span>
        <input
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSubmit()}
          placeholder="Enter command or speak..."
          className="flex-1 outline-none bg-transparent"
          style={{ ...raj, color: 'rgba(255,255,255,0.85)', fontSize: '13px' }}
        />
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={handleSubmit}
          disabled={!input.trim() || isTyping}
          className="w-7 h-7 rounded-lg flex items-center justify-center cursor-pointer"
          style={{
            background: input.trim() && !isTyping ? 'rgba(0,245,255,0.2)' : 'rgba(0,245,255,0.04)',
            border: `1px solid ${input.trim() && !isTyping ? 'rgba(0,245,255,0.5)' : 'rgba(0,245,255,0.1)'}`,
          }}
        >
          <Send className="w-3.5 h-3.5" style={{ color: input.trim() && !isTyping ? '#00f5ff' : 'rgba(0,245,255,0.3)' }} />
        </motion.button>
      </div>
    </div>
  );
}
