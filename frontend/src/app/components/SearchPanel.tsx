import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Search, Globe, Image, FileText, Clock, TrendingUp, X, ExternalLink } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { sendCommand } from '../services/jarvisApi';

const orb = { fontFamily: 'Orbitron, sans-serif' };
const mono = { fontFamily: 'Share Tech Mono, monospace' };
const raj = { fontFamily: 'Rajdhani, sans-serif' };

const MOCK_RESULTS: Record<string, { title: string; snippet: string; source: string; type: string }[]> = {
  default: [
    { title: 'JARVIS Documentation v3.7', snippet: 'Complete reference manual for JARVIS OS. Voice commands, gesture controls, API integration, memory management.', source: 'nexus.ai/docs', type: 'doc' },
    { title: 'Quantum Computing Advances 2026', snippet: 'New breakthroughs in error correction using topological qubits. Microsoft and IBM announce 1000+ logical qubit processors.', source: 'science.tech/quantum', type: 'article' },
    { title: 'Gemini 2.5 Model Performance Benchmark', snippet: 'Latest results show Gemini 2.5 outperforms GPT-5 on code generation, reasoning, and multimodal tasks by 23%.', source: 'ai.benchmark.io', type: 'report' },
    { title: 'Neural Interface Development', snippet: 'Brain-computer interface achieves 95% accuracy in thought-to-text translation using non-invasive EEG sensors.', source: 'neuro.research.org', type: 'paper' },
  ],
  quantum: [
    { title: 'Quantum Entanglement Breakthrough', snippet: 'Scientists achieve quantum entanglement over 1000km using satellite relays. Quantum internet one step closer.', source: 'physics.journal', type: 'paper' },
    { title: 'IBM Quantum Eagle Processor', snippet: '433-qubit processor achieves quantum advantage on optimization problems previously unsolvable classically.', source: 'ibm.com/quantum', type: 'article' },
  ],
  ai: [
    { title: 'GPT-6 Architecture Speculation', snippet: 'Leaked research suggests next OpenAI model will use 10T parameters with sparse activation. Training begins Q3 2026.', source: 'aiinsider.net', type: 'article' },
    { title: 'NEXUS Neural Core Architecture', snippet: 'Inside look at the modular design of JARVIS. Distributed inference across 48 neural processing units.', source: 'nexus.ai/blog', type: 'doc' },
  ],
};

const TRENDING = ['quantum computing', 'AI agents 2026', 'holographic UI', 'neural interfaces', 'space mining'];

const typeColors: Record<string, string> = {
  doc: '#00f5ff',
  article: '#a855f7',
  report: '#f59e0b',
  paper: '#0ea5e9',
};

export function SearchPanel() {
  const { addNotification } = useApp();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<typeof MOCK_RESULTS['default']>([]);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<'all' | 'images' | 'docs'>('all');
  const [history, setHistory] = useState(['system scan', 'neural networks', 'gemini api']);

  const search = (q: string) => {
    if (!q.trim()) { setResults([]); return; }
    setLoading(true);
    setTimeout(() => {
      const key = Object.keys(MOCK_RESULTS).find(k => q.toLowerCase().includes(k));
      setResults(key ? MOCK_RESULTS[key] : MOCK_RESULTS.default);
      setHistory(h => [q, ...h.filter(x => x !== q)].slice(0, 5));
      setLoading(false);
    }, 800 + Math.random() * 400);
  };

  const handleLaunchWebSearch = (searchQuery: string) => {
    const q = searchQuery.trim();
    if (!q) return;
    void sendCommand(`search ${q}`, 'search');
    addNotification({ type: 'info', title: 'Web Search', message: `Searching browser for "${q}"...` });
  };

  const handleSubmit = () => {
    if (query.trim()) search(query);
  };

  return (
    <div className="flex flex-col h-full gap-3 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4" style={{ color: '#0ea5e9' }} />
          <span style={{ ...orb, color: '#0ea5e9', fontSize: '11px', letterSpacing: '0.15em' }}>DATA SEARCH</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-1.5 h-1.5 rounded-full" style={{ background: '#22c55e', boxShadow: '0 0 4px #22c55e' }} />
          <span style={{ ...mono, color: 'rgba(34,197,94,0.7)', fontSize: '9px' }}>NEURAL CONNECTED</span>
        </div>
      </div>

      {/* Search bar */}
      <div
        className="flex items-center gap-2 rounded-xl px-3 py-2.5 flex-shrink-0"
        style={{
          background: 'rgba(0,8,25,0.7)',
          border: '1px solid rgba(14,165,233,0.25)',
        }}
      >
        <Search className="w-3.5 h-3.5 flex-shrink-0" style={{ color: 'rgba(14,165,233,0.6)' }} />
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSubmit()}
          placeholder="Search the datastream..."
          className="flex-1 outline-none bg-transparent"
          style={{ ...raj, color: 'rgba(255,255,255,0.85)', fontSize: '13px' }}
        />
        {query && (
          <button onClick={() => { setQuery(''); setResults([]); }} className="cursor-pointer">
            <X className="w-3.5 h-3.5" style={{ color: 'rgba(255,255,255,0.3)' }} />
          </button>
        )}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleSubmit}
          className="px-2.5 py-1.5 rounded-lg cursor-pointer flex items-center gap-1"
          style={{ background: 'rgba(14,165,233,0.2)', border: '1px solid rgba(14,165,233,0.4)' }}
        >
          <span style={{ ...mono, color: '#0ea5e9', fontSize: '10px' }}>GO</span>
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => handleLaunchWebSearch(query || 'JARVIS AI')}
          title="Search Google in browser"
          className="px-2.5 py-1.5 rounded-lg cursor-pointer flex items-center gap-1"
          style={{ background: 'rgba(34,197,94,0.15)', border: '1px solid rgba(34,197,94,0.4)' }}
        >
          <ExternalLink className="w-3 h-3" style={{ color: '#22c55e' }} />
          <span style={{ ...mono, color: '#22c55e', fontSize: '10px' }}>WEB</span>
        </motion.button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 flex-shrink-0">
        {[
          { id: 'all', icon: Globe, label: 'ALL' },
          { id: 'images', icon: Image, label: 'IMAGES' },
          { id: 'docs', icon: FileText, label: 'DOCS' },
        ].map(({ id, icon: Icon, label }) => (
          <motion.button
            key={id}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setTab(id as typeof tab)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg cursor-pointer"
            style={{
              background: tab === id ? 'rgba(14,165,233,0.15)' : 'rgba(14,165,233,0.04)',
              border: `1px solid ${tab === id ? 'rgba(14,165,233,0.4)' : 'rgba(14,165,233,0.12)'}`,
            }}
          >
            <Icon className="w-3 h-3" style={{ color: tab === id ? '#0ea5e9' : 'rgba(14,165,233,0.4)' }} />
            <span style={{ ...mono, color: tab === id ? '#0ea5e9' : 'rgba(14,165,233,0.4)', fontSize: '9px' }}>
              {label}
            </span>
          </motion.button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto flex flex-col gap-2 pr-1" style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(14,165,233,0.2) transparent' }}>
        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col gap-2">
              {[1, 2, 3].map(i => (
                <div key={i} className="rounded-xl p-3" style={{ background: 'rgba(0,8,25,0.5)', border: '1px solid rgba(14,165,233,0.1)' }}>
                  <div className="flex gap-2 mb-2">
                    <motion.div animate={{ opacity: [0.3, 0.6, 0.3] }} transition={{ duration: 1.5, repeat: Infinity }} className="h-3 rounded" style={{ background: 'rgba(14,165,233,0.2)', width: '60%' }} />
                    <motion.div animate={{ opacity: [0.3, 0.6, 0.3] }} transition={{ duration: 1.5, repeat: Infinity, delay: 0.2 }} className="h-3 rounded" style={{ background: 'rgba(14,165,233,0.1)', width: '20%' }} />
                  </div>
                  <motion.div animate={{ opacity: [0.2, 0.4, 0.2] }} transition={{ duration: 1.5, repeat: Infinity, delay: 0.1 }} className="h-2 rounded mb-1" style={{ background: 'rgba(14,165,233,0.15)', width: '90%' }} />
                  <motion.div animate={{ opacity: [0.2, 0.4, 0.2] }} transition={{ duration: 1.5, repeat: Infinity, delay: 0.15 }} className="h-2 rounded" style={{ background: 'rgba(14,165,233,0.1)', width: '75%' }} />
                </div>
              ))}
            </motion.div>
          ) : results.length > 0 ? (
            <motion.div key="results" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col gap-2">
              <span style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '9px' }}>
                {results.length} RESULTS FOR "{query.toUpperCase()}"
              </span>
              {results.map((r, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  onClick={() => handleLaunchWebSearch(r.title)}
                  className="rounded-xl p-3 group cursor-pointer"
                  style={{
                    background: 'rgba(0,8,25,0.5)',
                    border: '1px solid rgba(14,165,233,0.1)',
                    transition: 'border-color 0.2s, box-shadow 0.2s',
                  }}
                  onMouseEnter={e => {
                    (e.currentTarget as HTMLElement).style.borderColor = 'rgba(14,165,233,0.3)';
                    (e.currentTarget as HTMLElement).style.boxShadow = '0 0 12px rgba(14,165,233,0.06)';
                  }}
                  onMouseLeave={e => {
                    (e.currentTarget as HTMLElement).style.borderColor = 'rgba(14,165,233,0.1)';
                    (e.currentTarget as HTMLElement).style.boxShadow = 'none';
                  }}
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <span style={{ ...raj, color: 'rgba(220,240,255,0.9)', fontSize: '13px' }}>{r.title}</span>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <span
                        className="px-1.5 py-0.5 rounded"
                        style={{
                          background: `${typeColors[r.type]}15`,
                          border: `1px solid ${typeColors[r.type]}30`,
                          ...mono,
                          color: typeColors[r.type],
                          fontSize: '8px',
                        }}
                      >
                        {r.type.toUpperCase()}
                      </span>
                      <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" style={{ color: '#0ea5e9' }} />
                    </div>
                  </div>
                  <p style={{ ...raj, color: 'rgba(255,255,255,0.45)', fontSize: '11px', lineHeight: '1.5' }}>
                    {r.snippet}
                  </p>
                  <div className="flex items-center gap-1 mt-1.5">
                    <Globe className="w-2.5 h-2.5" style={{ color: 'rgba(14,165,233,0.5)' }} />
                    <span style={{ ...mono, color: 'rgba(14,165,233,0.6)', fontSize: '9px' }}>{r.source}</span>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          ) : (
            <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col gap-3">
              {/* Trending */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-3 h-3" style={{ color: 'rgba(14,165,233,0.6)' }} />
                  <span style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '9px' }}>TRENDING IN DATASTREAM</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {TRENDING.map(t => (
                    <motion.button
                      key={t}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => { setQuery(t); search(t); }}
                      className="px-2.5 py-1.5 rounded-lg cursor-pointer"
                      style={{ background: 'rgba(14,165,233,0.06)', border: '1px solid rgba(14,165,233,0.15)' }}
                    >
                      <span style={{ ...mono, color: 'rgba(14,165,233,0.7)', fontSize: '10px' }}>{t}</span>
                    </motion.button>
                  ))}
                </div>
              </div>

              {/* History */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Clock className="w-3 h-3" style={{ color: 'rgba(255,255,255,0.3)' }} />
                  <span style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '9px' }}>RECENT SEARCHES</span>
                </div>
                {history.map(h => (
                  <motion.button
                    key={h}
                    whileHover={{ x: 4 }}
                    onClick={() => { setQuery(h); search(h); }}
                    className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg cursor-pointer text-left"
                    style={{ background: 'transparent' }}
                  >
                    <Clock className="w-3 h-3" style={{ color: 'rgba(255,255,255,0.2)' }} />
                    <span style={{ ...raj, color: 'rgba(255,255,255,0.5)', fontSize: '12px' }}>{h}</span>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
