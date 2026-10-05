import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  X, User, Brain, Key, Shield, Eye, EyeOff, ChevronDown,
  CheckCircle, AlertCircle, Save, RotateCcw, Lock, Loader2
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { getSettings, saveSettings } from '../services/jarvisApi';

const orb = { fontFamily: 'Orbitron, sans-serif' };
const mono = { fontFamily: 'Share Tech Mono, monospace' };
const raj = { fontFamily: 'Rajdhani, sans-serif' };

type Section = 'user' | 'ai' | 'api' | 'security';

const SECTIONS: { id: Section; label: string; icon: React.ElementType; color: string }[] = [
  { id: 'user', label: 'USER PROFILE', icon: User, color: '#00f5ff' },
  { id: 'ai', label: 'AI MODEL', icon: Brain, color: '#a855f7' },
  { id: 'api', label: 'API KEYS', icon: Key, color: '#f59e0b' },
  { id: 'security', label: 'SECURITY', icon: Shield, color: '#22c55e' },
];

const AI_MODELS = ['Gemini 2.5 Pro', 'Gemini 2.0 Flash', 'GPT-4o', 'Claude 3.5 Sonnet', 'Llama 3.3 70B', 'Mistral Large'];

function Field({ label, value, onChange, type = 'text', placeholder = '' }: {
  label: string; value: string; onChange: (v: string) => void;
  type?: string; placeholder?: string;
}) {
  const [show, setShow] = useState(false);
  const isSecret = type === 'password';

  return (
    <div className="flex flex-col gap-1.5">
      <label style={{ ...mono, color: 'rgba(255,255,255,0.4)', fontSize: '10px' }}>{label}</label>
      <div
        className="flex items-center gap-2 rounded-xl px-3 py-2.5"
        style={{
          background: 'rgba(0,5,15,0.7)',
          border: '1px solid rgba(255,255,255,0.08)',
          transition: 'border-color 0.2s',
        }}
        onFocusCapture={e => (e.currentTarget.style.borderColor = 'rgba(0,245,255,0.3)')}
        onBlurCapture={e => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)')}
      >
        <input
          type={isSecret && !show ? 'password' : 'text'}
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          className="flex-1 bg-transparent outline-none"
          style={{ ...raj, color: 'rgba(255,255,255,0.85)', fontSize: '13px' }}
        />
        {isSecret && (
          <button onClick={() => setShow(!show)} className="cursor-pointer">
            {show ? (
              <EyeOff className="w-4 h-4" style={{ color: 'rgba(255,255,255,0.3)' }} />
            ) : (
              <Eye className="w-4 h-4" style={{ color: 'rgba(255,255,255,0.3)' }} />
            )}
          </button>
        )}
      </div>
    </div>
  );
}

function Toggle({ label, value, onChange, color = '#00f5ff' }: {
  label: string; value: boolean; onChange: (v: boolean) => void; color?: string;
}) {
  return (
    <div className="flex items-center justify-between py-2">
      <span style={{ ...raj, color: 'rgba(255,255,255,0.7)', fontSize: '13px' }}>{label}</span>
      <motion.button
        onClick={() => onChange(!value)}
        className="w-11 h-6 rounded-full relative cursor-pointer"
        style={{ background: value ? `${color}30` : 'rgba(255,255,255,0.06)', border: `1px solid ${value ? color : 'rgba(255,255,255,0.12)'}` }}
      >
        <motion.div
          animate={{ x: value ? 20 : 2 }}
          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
          className="absolute top-0.5 w-5 h-5 rounded-full"
          style={{ background: value ? color : 'rgba(255,255,255,0.3)', boxShadow: value ? `0 0 8px ${color}` : 'none' }}
        />
      </motion.button>
    </div>
  );
}

export function SettingsPanel() {
  const { settingsOpen, setSettingsOpen, addNotification } = useApp();
  const [section, setSection] = useState<Section>('user');
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  // User settings
  const [username, setUsername] = useState('nexus_user');
  const [fullName, setFullName] = useState('Alex Morgan');
  const [assistantName, setAssistantName] = useState('JARVIS');

  // AI settings
  const [model, setModel] = useState(AI_MODELS[0]);
  const [modelOpen, setModelOpen] = useState(false);
  const [temperature, setTemperature] = useState(0.7);
  const [streaming, setStreaming] = useState(true);
  const [voiceEnabled, setVoiceEnabled] = useState(true);

  // API keys
  const [geminiKey, setGeminiKey] = useState('AIza••••••••••••••••••••••••••');
  const [secretKey, setSecretKey] = useState('sk-••••••••••••••••••••••••••••');
  const [gitUrl, setGitUrl] = useState('https://github.com/nexus-ai/config');
  const [weatherKey, setWeatherKey] = useState('wk_••••••••••••••');
  const [searchId, setSearchId] = useState('cx_••••••••••••');

  // Security
  const [encEnabled, setEncEnabled] = useState(true);
  const [biometrics, setBiometrics] = useState(true);
  const [twoFactor, setTwoFactor] = useState(true);
  const [auditLog, setAuditLog] = useState(true);

  // Load settings from backend on mount
  useEffect(() => {
    const load = async () => {
      try {
        const response = await getSettings();
        if (response.ok && response.settings) {
          const s = response.settings as Record<string, unknown>;
          // User
          if (s.username) setUsername(String(s.username));
          if (s.fullName) setFullName(String(s.fullName));
          if (s.assistantName) setAssistantName(String(s.assistantName));
          // AI
          if (s.model) setModel(String(s.model));
          if (typeof s.temperature === 'number') setTemperature(s.temperature);
          if (typeof s.streaming === 'boolean') setStreaming(s.streaming);
          if (typeof s.voiceEnabled === 'boolean') setVoiceEnabled(s.voiceEnabled);
          // API
          if (s.geminiKey) setGeminiKey(String(s.geminiKey));
          if (s.secretKey) setSecretKey(String(s.secretKey));
          if (s.gitUrl) setGitUrl(String(s.gitUrl));
          if (s.weatherKey) setWeatherKey(String(s.weatherKey));
          if (s.searchId) setSearchId(String(s.searchId));
          // Security
          if (typeof s.encEnabled === 'boolean') setEncEnabled(s.encEnabled);
          if (typeof s.biometrics === 'boolean') setBiometrics(s.biometrics);
          if (typeof s.twoFactor === 'boolean') setTwoFactor(s.twoFactor);
          if (typeof s.auditLog === 'boolean') setAuditLog(s.auditLog);
        }
      } catch (e) {
        console.warn('Failed to load settings:', e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleSave = async () => {
    const settings = {
      username,
      fullName,
      assistantName,
      model,
      temperature,
      streaming,
      voiceEnabled,
      geminiKey,
      secretKey,
      gitUrl,
      weatherKey,
      searchId,
      encEnabled,
      biometrics,
      twoFactor,
      auditLog,
    };
    try {
      const response = await saveSettings(settings);
      if (response.ok) {
        setSaved(true);
        addNotification({ type: 'success', title: 'Settings Saved', message: 'All configuration changes applied successfully.' });
        setTimeout(() => setSaved(false), 3000);
      } else {
        addNotification({ type: 'error', title: 'Save Failed', message: response.message ?? 'Could not save settings.' });
      }
    } catch (e) {
      addNotification({ type: 'error', title: 'Save Failed', message: 'Unable to reach the JARVIS service.' });
    }
  };

  return (
    <AnimatePresence>
      {settingsOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 flex items-center justify-center"
          style={{ zIndex: 180, background: 'rgba(0, 4, 12, 0.92)', backdropFilter: 'blur(12px)' }}
        >
          <motion.div
            initial={{ scale: 0.92, y: 16 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.92, y: 16 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            className="w-full max-w-3xl mx-6 rounded-2xl overflow-hidden flex flex-col"
            style={{
              maxHeight: '85vh',
              background: 'rgba(0, 10, 25, 0.95)',
              border: '1px solid rgba(0,245,255,0.2)',
              boxShadow: '0 0 60px rgba(0,245,255,0.1)',
            }}
          >
            {/* Header */}
            <div
              className="flex items-center justify-between px-8 py-5 flex-shrink-0"
              style={{ borderBottom: '1px solid rgba(0,245,255,0.12)' }}
            >
              <div>
                <h2 style={{ ...orb, color: '#00f5ff', fontSize: '16px', letterSpacing: '0.2em', margin: 0 }}>
                  SYSTEM CONFIGURATION
                </h2>
                <p style={{ ...mono, color: 'rgba(0,245,255,0.4)', fontSize: '10px', marginTop: 4 }}>
                  JARVIS OS v3.7.2 — Advanced Settings
                </p>
              </div>
              <motion.button
                whileHover={{ scale: 1.1, rotate: 90 }}
                whileTap={{ scale: 0.9 }}
                onClick={() => setSettingsOpen(false)}
                className="w-10 h-10 rounded-xl flex items-center justify-center cursor-pointer"
                style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)' }}
              >
                <X className="w-5 h-5" style={{ color: '#ef4444' }} />
              </motion.button>
            </div>

            <div className="flex flex-1 overflow-hidden">
              {/* Sidebar */}
              <div
                className="w-52 flex flex-col gap-1 p-4 flex-shrink-0"
                style={{ borderRight: '1px solid rgba(0,245,255,0.08)' }}
              >
                {SECTIONS.map(s => (
                  <motion.button
                    key={s.id}
                    whileHover={{ x: 2 }}
                    onClick={() => setSection(s.id)}
                    className="flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer text-left"
                    style={{
                      background: section === s.id ? `${s.color}12` : 'transparent',
                      border: `1px solid ${section === s.id ? `${s.color}30` : 'transparent'}`,
                    }}
                  >
                    <s.icon className="w-4 h-4" style={{ color: section === s.id ? s.color : 'rgba(255,255,255,0.3)' }} />
                    <span style={{ ...mono, color: section === s.id ? s.color : 'rgba(255,255,255,0.4)', fontSize: '10px' }}>
                      {s.label}
                    </span>
                  </motion.button>
                ))}
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-8" style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(0,245,255,0.2) transparent' }}>
                <AnimatePresence mode="wait">
                  {section === 'user' && (
                    <motion.div key="user" initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -10 }} className="flex flex-col gap-4">
                      <div className="flex flex-col gap-4">
                        {/* Avatar placeholder */}
                        <div className="flex items-center gap-4 mb-2">
                          <div
                            className="w-16 h-16 rounded-2xl flex items-center justify-center"
                            style={{ background: 'rgba(0,245,255,0.08)', border: '1px solid rgba(0,245,255,0.2)' }}
                          >
                            <User className="w-8 h-8" style={{ color: '#00f5ff' }} />
                          </div>
                          <div>
                            <p style={{ ...raj, color: 'rgba(255,255,255,0.8)', fontSize: '16px' }}>{fullName}</p>
                            <p style={{ ...mono, color: 'rgba(0,245,255,0.6)', fontSize: '11px' }}>@{username}</p>
                          </div>
                        </div>
                        <Field label="USERNAME" value={username} onChange={setUsername} placeholder="nexus_user" />
                        <Field label="FULL NAME" value={fullName} onChange={setFullName} placeholder="Your Name" />
                        <Field label="ASSISTANT NAME" value={assistantName} onChange={setAssistantName} placeholder="JARVIS" />
                      </div>
                    </motion.div>
                  )}

                  {section === 'ai' && (
                    <motion.div key="ai" initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -10 }} className="flex flex-col gap-4">
                      <div className="flex flex-col gap-1.5">
                        <label style={{ ...mono, color: 'rgba(255,255,255,0.4)', fontSize: '10px' }}>AI MODEL</label>
                        <div className="relative">
                          <button
                            onClick={() => setModelOpen(!modelOpen)}
                            className="w-full flex items-center justify-between rounded-xl px-3 py-2.5 cursor-pointer"
                            style={{ background: 'rgba(0,5,15,0.7)', border: '1px solid rgba(168,85,247,0.25)' }}
                          >
                            <span style={{ ...raj, color: 'rgba(255,255,255,0.85)', fontSize: '13px' }}>{model}</span>
                            <ChevronDown className="w-4 h-4" style={{ color: 'rgba(168,85,247,0.6)', transform: modelOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
                          </button>
                          <AnimatePresence>
                            {modelOpen && (
                              <motion.div
                                initial={{ opacity: 0, y: -4 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -4 }}
                                className="absolute top-full left-0 right-0 mt-1 rounded-xl overflow-hidden z-10"
                                style={{ background: 'rgba(0,10,25,0.98)', border: '1px solid rgba(168,85,247,0.25)' }}
                              >
                                {AI_MODELS.map(m => (
                                  <button
                                    key={m}
                                    onClick={() => { setModel(m); setModelOpen(false); }}
                                    className="w-full px-4 py-2.5 text-left cursor-pointer hover:bg-purple-500/10 transition-colors"
                                    style={{ borderBottom: '1px solid rgba(168,85,247,0.08)' }}
                                  >
                                    <span style={{ ...raj, color: m === model ? '#a855f7' : 'rgba(255,255,255,0.6)', fontSize: '13px' }}>
                                      {m}
                                    </span>
                                  </button>
                                ))}
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      </div>

                      {/* Temperature slider */}
                      <div className="flex flex-col gap-1.5">
                        <div className="flex justify-between">
                          <label style={{ ...mono, color: 'rgba(255,255,255,0.4)', fontSize: '10px' }}>TEMPERATURE</label>
                          <span style={{ ...mono, color: '#a855f7', fontSize: '10px' }}>{temperature.toFixed(2)}</span>
                        </div>
                        <input
                          type="range" min="0" max="1" step="0.01"
                          value={temperature}
                          onChange={e => setTemperature(parseFloat(e.target.value))}
                          className="w-full accent-purple-500"
                        />
                      </div>

                      {/* Performance bar */}
                      <div className="rounded-xl p-3" style={{ background: 'rgba(168,85,247,0.06)', border: '1px solid rgba(168,85,247,0.15)' }}>
                        <div className="flex items-center justify-between mb-2">
                          <span style={{ ...mono, color: 'rgba(255,255,255,0.4)', fontSize: '10px' }}>MODEL PERFORMANCE</span>
                          <span style={{ ...mono, color: '#22c55e', fontSize: '10px' }}>OPTIMAL</span>
                        </div>
                        {[
                          { label: 'Speed', val: 94 },
                          { label: 'Accuracy', val: 98 },
                          { label: 'Context', val: 87 },
                        ].map(m => (
                          <div key={m.label} className="flex items-center gap-3 mb-1.5">
                            <span style={{ ...mono, color: 'rgba(255,255,255,0.35)', fontSize: '9px', width: 55 }}>{m.label}</span>
                            <div className="flex-1 h-1 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                              <div className="h-full rounded-full" style={{ width: `${m.val}%`, background: '#a855f7', boxShadow: '0 0 4px #a855f7' }} />
                            </div>
                            <span style={{ ...mono, color: '#a855f7', fontSize: '9px' }}>{m.val}%</span>
                          </div>
                        ))}
                      </div>

                      <Toggle label="Streaming Responses" value={streaming} onChange={setStreaming} color="#a855f7" />
                      <Toggle label="Voice Integration" value={voiceEnabled} onChange={setVoiceEnabled} color="#a855f7" />
                    </motion.div>
                  )}

                  {section === 'api' && (
                    <motion.div key="api" initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -10 }} className="flex flex-col gap-4">
                      <Field label="GEMINI API KEY" value={geminiKey} onChange={setGeminiKey} type="password" placeholder="AIza..." />
                      <Field label="SECRET KEY" value={secretKey} onChange={setSecretKey} type="password" placeholder="sk-..." />
                      <Field label="GIT SYNC URL" value={gitUrl} onChange={setGitUrl} placeholder="https://github.com/..." />
                      <Field label="OPENWEATHER API KEY" value={weatherKey} onChange={setWeatherKey} type="password" placeholder="wk_..." />
                      <Field label="CUSTOM SEARCH ENGINE ID" value={searchId} onChange={setSearchId} type="password" placeholder="cx_..." />

                      <div className="rounded-xl p-3" style={{ background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.15)' }}>
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4" style={{ color: '#f59e0b' }} />
                          <span style={{ ...mono, color: 'rgba(245,158,11,0.8)', fontSize: '10px' }}>API KEYS ARE ENCRYPTED AND STORED LOCALLY</span>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {section === 'security' && (
                    <motion.div key="security" initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -10 }} className="flex flex-col gap-2">
                      {/* Encryption status */}
                      <div className="rounded-xl p-4 mb-2" style={{ background: 'rgba(34,197,94,0.06)', border: '1px solid rgba(34,197,94,0.2)' }}>
                        <div className="flex items-center gap-3">
                          <Lock className="w-5 h-5" style={{ color: '#22c55e' }} />
                          <div>
                            <p style={{ ...raj, color: 'rgba(255,255,255,0.8)', fontSize: '14px' }}>Encryption Active</p>
                            <p style={{ ...mono, color: 'rgba(34,197,94,0.7)', fontSize: '10px' }}>AES-256-GCM + RSA-4096 — All channels secured</p>
                          </div>
                          <CheckCircle className="w-4 h-4 ml-auto" style={{ color: '#22c55e' }} />
                        </div>
                      </div>

                      <Toggle label="End-to-End Encryption" value={encEnabled} onChange={setEncEnabled} color="#22c55e" />
                      <Toggle label="Biometric Authentication" value={biometrics} onChange={setBiometrics} color="#22c55e" />
                      <Toggle label="Two-Factor Authentication" value={twoFactor} onChange={setTwoFactor} color="#22c55e" />
                      <Toggle label="Audit Logging" value={auditLog} onChange={setAuditLog} color="#22c55e" />

                      <div className="rounded-xl p-3 mt-2" style={{ background: 'rgba(0,5,15,0.5)', border: '1px solid rgba(34,197,94,0.1)' }}>
                        {[
                          { label: 'Last Login', val: '2026-04-02 09:14:32 UTC' },
                          { label: 'Active Sessions', val: '1 (This device)' },
                          { label: 'Key Rotation', val: '15 days ago' },
                          { label: 'Threat Level', val: 'None detected' },
                        ].map(({ label, val }) => (
                          <div key={label} className="flex items-center justify-between py-1.5" style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                            <span style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '10px' }}>{label}</span>
                            <span style={{ ...mono, color: 'rgba(34,197,94,0.7)', fontSize: '10px' }}>{val}</span>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            {/* Footer */}
            <div
              className="flex items-center justify-end gap-3 px-8 py-4 flex-shrink-0"
              style={{ borderTop: '1px solid rgba(0,245,255,0.08)' }}
            >
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setSettingsOpen(false)}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 rounded-xl cursor-pointer"
                style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', opacity: loading ? 0.5 : 1 }}
              >
                <RotateCcw className="w-3.5 h-3.5" style={{ color: 'rgba(255,255,255,0.4)' }} />
                <span style={{ ...mono, color: 'rgba(255,255,255,0.4)', fontSize: '10px' }}>CANCEL</span>
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleSave}
                disabled={loading}
                className="flex items-center gap-2 px-5 py-2 rounded-xl cursor-pointer"
                style={{
                  background: loading ? 'rgba(0,245,255,0.12)' : saved ? 'rgba(34,197,94,0.15)' : 'rgba(0,245,255,0.12)',
                  border: `1px solid ${loading || saved ? 'rgba(0,245,255,0.35)' : 'rgba(0,245,255,0.35)'}`,
                  boxShadow: loading ? '0 0 12px rgba(0,245,255,0.1)' : saved ? '0 0 12px rgba(34,197,94,0.2)' : '0 0 12px rgba(0,245,255,0.1)',
                }}
              >
                {loading ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" style={{ color: '#00f5ff' }} />
                ) : saved ? (
                  <CheckCircle className="w-3.5 h-3.5" style={{ color: '#22c55e' }} />
                ) : (
                  <Save className="w-3.5 h-3.5" style={{ color: '#00f5ff' }} />
                )}
                <span style={{ ...mono, color: loading ? '#00f5ff' : saved ? '#22c55e' : '#00f5ff', fontSize: '10px' }}>
                  {loading ? 'SAVING...' : saved ? 'SAVED' : 'SAVE CHANGES'}
                </span>
              </motion.button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
