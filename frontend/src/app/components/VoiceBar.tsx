import React, { useCallback, useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { Mic, Type, Volume2 } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { getApiBaseUrl, sendCommand, startVoiceRecognition, stopVoiceRecognition } from '../services/jarvisApi';

const mono = { fontFamily: 'Share Tech Mono, monospace' };
const raj = { fontFamily: 'Rajdhani, sans-serif' };
const BAR_COUNT = 32;

export function VoiceBar() {
  const { aiState, setAiState, addMessage, addNotification, setScanningActive, setSettingsOpen, setAppGridOpen, setGestureOpen, setPendingConfirmation } = useApp();
  const [textMode, setTextMode] = useState(false);
  const [input, setInput] = useState('');
  const [bars, setBars] = useState(() => Array(BAR_COUNT).fill(0.15));
  const [transcript, setTranscript] = useState('');
  const [voiceConnected, setVoiceConnected] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isListening = aiState === 'listening';
  const isProcessing = aiState === 'processing' || aiState === 'responding';

  const runCommand = useCallback(async (text: string, source: 'voice' | 'voice-text') => {
    const command = text.trim();
    if (!command) return;
    setTranscript(command);
    addMessage({ type: 'user', text: command });
    setAiState('processing');
    try {
      const response = await sendCommand(command, source);
      addMessage({ type: 'ai', text: response.message });
      if (response.requires_confirmation && response.confirmation) {
        setPendingConfirmation({ ...response.confirmation, source });
        addNotification({ type: 'warning', title: 'Confirmation Required', message: response.confirmation.message });
      }
      if (response.action === 'scan') setScanningActive(true);
      if (response.action === 'settings') setSettingsOpen(true);
      if (response.action === 'apps') setAppGridOpen(true);
      if (response.action === 'gesture') setGestureOpen(true);
      setAiState('responding');
      const spokenDuration = Math.min(Math.max((response.message?.length || 20) * 60, 2500), 8000);
      setTimeout(() => {
        setAiState(voiceConnected ? 'listening' : 'idle');
      }, spokenDuration);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to process the command.';
      addMessage({ type: 'ai', text: message });
      addNotification({ type: 'error', title: 'Command Failed', message });
      setAiState(voiceConnected ? 'listening' : 'idle');
    }
  }, [addMessage, addNotification, setAiState, setAppGridOpen, setGestureOpen, setPendingConfirmation, setScanningActive, setSettingsOpen, voiceConnected]);

  useEffect(() => {
    const stream = new EventSource(`${getApiBaseUrl()}/api/voice/stream`);
    stream.onmessage = event => {
      try {
        const data = JSON.parse(event.data) as { type: string; text?: string; message?: string; listening?: boolean };
        if (data.type === 'status') {
          setVoiceConnected(Boolean(data.listening));
          if (data.listening) setAiState('listening');
        } else if (data.type === 'wake') {
          setVoiceConnected(true);
          setAiState('listening');
          addNotification({ type: 'info', title: 'Wake Detected', message: `Triggered: ${(data as any).phrase || "Daddy's home"}` });
        } else if (data.type === 'transcript' && data.text) {
          void runCommand(data.text, 'voice');
        } else if (data.type === 'error') {
          setVoiceConnected(false);
          setAiState('idle');
          addNotification({ type: 'error', title: 'Voice Recognition', message: data.message ?? 'Voice recognition stopped.' });
        }
      } catch {
        setVoiceConnected(false);
      }
    };
    stream.onerror = () => setVoiceConnected(false);
    return () => stream.close();
  }, [addNotification, runCommand, setAiState]);

  useEffect(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (isListening) {
      let phase = 0;
      intervalRef.current = setInterval(() => {
        phase += 0.42;
        setBars(Array.from({ length: BAR_COUNT }, (_, index) => {
          const center = Math.abs(index - BAR_COUNT / 2) / (BAR_COUNT / 2);
          return 0.18 + (Math.sin(phase + index * 0.55) + 1) * 0.28 * (1 - center * 0.45);
        }));
      }, 80);
    } else if (isProcessing) {
      intervalRef.current = setInterval(() => setBars(Array.from({ length: BAR_COUNT }, (_, index) => 0.22 + 0.35 * Math.abs(Math.sin(Date.now() / 200 + index * 0.3)))), 80);
    } else {
      setBars(Array(BAR_COUNT).fill(0.15));
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [isListening, isProcessing]);

  const toggleListening = async () => {
    if (voiceConnected || isListening) {
      await stopVoiceRecognition();
      setVoiceConnected(false);
      setAiState('idle');
      setTranscript('');
      return;
    }
    try {
      const response = await startVoiceRecognition();
      if (!response.ok) throw new Error(response.message);
      setVoiceConnected(true);
      setAiState('listening');
      setTranscript('');
      addNotification({ type: 'info', title: 'Voice Active', message: 'Listening locally through Windows Speech Recognition.' });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to start voice recognition.';
      addNotification({ type: 'error', title: 'Microphone Unavailable', message });
    }
  };

  const submitText = () => {
    const command = input.trim();
    if (!command) return;
    setInput('');
    void runCommand(command, 'voice-text');
  };

  const stateColor = { idle: '#00f5ff', listening: '#22c55e', processing: '#f59e0b', responding: '#a855f7' }[aiState];

  return <div className="fixed left-0 right-0 flex items-center px-6 gap-4" style={{ bottom: 72, height: 72, zIndex: 60, background: 'rgba(1, 8, 20, 0.85)', backdropFilter: 'blur(20px)', borderTop: '1px solid rgba(0, 245, 255, 0.1)', borderBottom: '1px solid rgba(0, 245, 255, 0.06)' }}>
    <motion.button whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }} onClick={() => setTextMode(value => !value)} className="w-10 h-10 rounded-xl flex items-center justify-center cursor-pointer flex-shrink-0" style={{ background: textMode ? 'rgba(168,85,247,0.15)' : 'rgba(0,245,255,0.05)', border: `1px solid ${textMode ? 'rgba(168,85,247,0.4)' : 'rgba(0,245,255,0.15)'}` }}>{textMode ? <Type className="w-4 h-4" style={{ color: '#a855f7' }} /> : <Volume2 className="w-4 h-4" style={{ color: '#00f5ff' }} />}</motion.button>
    <AnimatePresence mode="wait">
      {!textMode ? <motion.div key="voice" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1 flex items-center gap-4"><div className="flex-1 flex items-center justify-center gap-0.5 h-12 overflow-hidden">{bars.map((height, index) => <motion.div key={index} animate={{ scaleY: height }} transition={{ duration: 0.08, ease: 'linear' }} className="rounded-full origin-center flex-shrink-0" style={{ width: 2.5, height: '100%', background: isListening ? `rgba(34, 197, 94, ${0.35 + height * 0.55})` : isProcessing ? `rgba(245, 158, 11, ${0.3 + height * 0.5})` : `rgba(0, 245, 255, ${0.1 + height * 0.3})` }} />)}</div>{transcript && <span className="flex-shrink-0 max-w-48 truncate" style={{ ...raj, color: 'rgba(255,255,255,0.7)', fontSize: '12px' }}>{transcript}</span>}</motion.div> : <motion.div key="text" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1 flex items-center gap-2"><div className="flex-1 flex items-center gap-2 rounded-xl px-4 py-2" style={{ background: 'rgba(0,8,25,0.6)', border: '1px solid rgba(168,85,247,0.2)' }}><span style={{ ...mono, color: 'rgba(168,85,247,0.5)', fontSize: '12px' }}>&gt;</span><input value={input} onChange={event => setInput(event.target.value)} onKeyDown={event => event.key === 'Enter' && submitText()} placeholder="Type a command..." className="flex-1 outline-none bg-transparent" style={{ ...raj, color: 'rgba(255,255,255,0.85)', fontSize: '13px' }} /></div></motion.div>}
    </AnimatePresence>
    <div className="flex flex-col items-center gap-1 flex-shrink-0"><span style={{ ...mono, color: stateColor, fontSize: '8px', letterSpacing: '0.1em' }}>{aiState.toUpperCase()}</span><motion.button onClick={() => void toggleListening()} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.9 }} className="relative w-12 h-12 rounded-full flex items-center justify-center cursor-pointer" style={{ background: isListening ? 'rgba(34, 197, 94, 0.15)' : isProcessing ? 'rgba(245, 158, 11, 0.1)' : 'rgba(0, 245, 255, 0.08)', border: `2px solid ${stateColor}`, boxShadow: `0 0 20px ${stateColor}40, 0 0 40px ${stateColor}15` }}>{isListening && <motion.div animate={{ scale: [1, 1.9, 1], opacity: [0.4, 0, 0.4] }} transition={{ duration: 1.2, repeat: Infinity }} className="absolute inset-0 rounded-full" style={{ border: '2px solid rgba(34,197,94,0.5)' }} />}{isProcessing ? <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}><div className="w-4 h-4 rounded-full border-2 border-transparent" style={{ borderTopColor: '#f59e0b', borderRightColor: '#f59e0b40' }} /></motion.div> : <Mic className="w-5 h-5" style={{ color: isListening ? '#22c55e' : '#00f5ff' }} />}</motion.button></div>
  </div>;
}
