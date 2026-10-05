import { AnimatePresence, motion } from 'motion/react';
import { AlertTriangle, Check, X } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { cancelCommand, confirmCommand } from '../services/jarvisApi';

const mono = { fontFamily: 'Share Tech Mono, monospace' };
const raj = { fontFamily: 'Rajdhani, sans-serif' };

export function ConfirmationDialog() {
  const { pendingConfirmation, setPendingConfirmation, addMessage, addNotification } = useApp();
  const confirm = async () => {
    if (!pendingConfirmation) return;
    try {
      const result = await confirmCommand(pendingConfirmation.action, pendingConfirmation.target, pendingConfirmation.source);
      addMessage({ type: 'ai', text: result.message });
      addNotification({ type: result.ok ? 'success' : 'error', title: 'Action Confirmation', message: result.message });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to complete the approved action.';
      addNotification({ type: 'error', title: 'Action Failed', message });
    } finally { setPendingConfirmation(null); }
  };
  const cancel = async () => {
    if (!pendingConfirmation) return;
    try { await cancelCommand(pendingConfirmation.action, pendingConfirmation.target, pendingConfirmation.source); }
    finally { setPendingConfirmation(null); }
  };
  return <AnimatePresence>{pendingConfirmation && <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-[400] flex items-center justify-center p-6" style={{ background: 'rgba(0,5,15,0.78)', backdropFilter: 'blur(8px)' }}><motion.div initial={{ scale: 0.94, y: 12 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.94, y: 12 }} className="w-full max-w-sm rounded-2xl p-5" style={{ background: 'rgba(5,12,28,0.98)', border: '1px solid rgba(245,158,11,0.45)', boxShadow: '0 0 40px rgba(245,158,11,0.12)' }}><div className="flex items-start gap-3"><AlertTriangle className="w-5 h-5 flex-shrink-0" style={{ color: '#f59e0b' }} /><div><h2 style={{ ...mono, color: '#f59e0b', fontSize: '12px', margin: 0 }}>{pendingConfirmation.title.toUpperCase()}</h2><p style={{ ...raj, color: 'rgba(255,255,255,0.7)', fontSize: '14px', marginTop: 8 }}>{pendingConfirmation.message}</p><p style={{ ...mono, color: 'rgba(255,255,255,0.35)', fontSize: '9px', marginTop: 8 }}>THIS ACTION WILL BE RECORDED LOCALLY.</p></div></div><div className="flex gap-2 mt-5"><button onClick={() => void cancel()} className="flex-1 py-2 rounded-lg cursor-pointer" style={{ ...mono, fontSize: '10px', color: 'rgba(255,255,255,0.65)', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.12)' }}><X className="w-3 h-3 inline mr-1" />CANCEL</button><button onClick={() => void confirm()} className="flex-1 py-2 rounded-lg cursor-pointer" style={{ ...mono, fontSize: '10px', color: '#f59e0b', background: 'rgba(245,158,11,0.12)', border: '1px solid rgba(245,158,11,0.4)' }}><Check className="w-3 h-3 inline mr-1" />APPROVE</button></div></motion.div></motion.div>}</AnimatePresence>;
}
