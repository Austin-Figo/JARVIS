import React, { useEffect, useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { Brain, Clock, Edit, Loader2, Plus, Tag, Trash2, X } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { createMemory, deleteMemory, getMemories, type MemoryItem, updateMemory } from '../services/jarvisApi';

const orb = { fontFamily: 'Orbitron, sans-serif' };
const mono = { fontFamily: 'Share Tech Mono, monospace' };
const raj = { fontFamily: 'Rajdhani, sans-serif' };

type FormState = { title: string; content: string; tags: string; synced: boolean };
const emptyForm: FormState = { title: '', content: '', tags: '', synced: false };

export function MemoryPanel() {
  const { addNotification } = useApp();
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTag, setActiveTag] = useState<string | null>(null);
  const [modal, setModal] = useState<'create' | 'edit' | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);

  const loadMemories = async () => {
    setLoading(true);
    try {
      const response = await getMemories();
      setMemories(response.memories);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to load memories.';
      addNotification({ type: 'error', title: 'Memory Offline', message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void loadMemories(); }, []);

  const tags = useMemo(() => [...new Set(memories.flatMap(memory => memory.tags))].sort(), [memories]);
  const visibleMemories = activeTag ? memories.filter(memory => memory.tags.includes(activeTag)) : memories;

  const formatTime = (timestamp: number) => {
    const diff = Math.max(0, Date.now() - timestamp);
    if (diff < 3_600_000) return `${Math.max(1, Math.floor(diff / 60_000))}m ago`;
    if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
    return `${Math.floor(diff / 86_400_000)}d ago`;
  };

  const closeModal = () => { setModal(null); setEditingId(null); setForm(emptyForm); };
  const openCreate = () => { setEditingId(null); setForm(emptyForm); setModal('create'); };
  const openEdit = (memory: MemoryItem) => {
    setEditingId(memory.id);
    setForm({ title: memory.title, content: memory.content, tags: memory.tags.join(', '), synced: memory.synced });
    setModal('edit');
  };

  const saveMemory = async () => {
    const title = form.title.trim();
    const content = form.content.trim();
    const parsedTags = form.tags.split(',').map(tag => tag.trim()).filter(Boolean);
    if (!title || !content) {
      addNotification({ type: 'warning', title: 'Missing Information', message: 'A title and content are required.' });
      return;
    }
    setLoading(true);
    try {
      if (modal === 'edit' && editingId) {
        const response = await updateMemory(editingId, { title, content, tags: parsedTags, synced: form.synced });
        setMemories(previous => previous.map(memory => memory.id === editingId ? response.memory : memory));
        addNotification({ type: 'success', title: 'Memory Updated', message: 'Memory saved successfully.' });
      } else {
        const response = await createMemory(title, content, parsedTags, form.synced);
        setMemories(previous => [response.memory, ...previous]);
        addNotification({ type: 'success', title: 'Memory Created', message: 'New memory stored locally.' });
      }
      closeModal();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to save memory.';
      addNotification({ type: 'error', title: 'Save Failed', message });
    } finally {
      setLoading(false);
    }
  };

  const removeMemory = async (id: string) => {
    try {
      await deleteMemory(id);
      setMemories(previous => previous.filter(memory => memory.id !== id));
      addNotification({ type: 'success', title: 'Memory Deleted', message: 'Memory removed.' });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to delete memory.';
      addNotification({ type: 'error', title: 'Delete Failed', message });
    }
  };

  return (
    <div className="flex flex-col h-full gap-3 overflow-hidden">
      <div className="flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4" style={{ color: '#a855f7' }} />
          <span style={{ ...orb, color: '#a855f7', fontSize: '11px', letterSpacing: '0.15em' }}>MEMORY CORE</span>
        </div>
        <motion.button whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }} onClick={openCreate} className="p-1.5 rounded-lg cursor-pointer" style={{ background: 'rgba(168,85,247,0.08)', border: '1px solid rgba(168,85,247,0.25)' }} aria-label="Add memory">
          <Plus className="w-3.5 h-3.5" style={{ color: '#a855f7' }} />
        </motion.button>
      </div>

      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 flex-shrink-0">
          <motion.button whileTap={{ scale: 0.95 }} onClick={() => setActiveTag(null)} className="px-2 py-1 rounded-md cursor-pointer" style={{ ...mono, fontSize: '9px', color: activeTag === null ? '#a855f7' : 'rgba(168,85,247,0.65)', background: activeTag === null ? 'rgba(168,85,247,0.2)' : 'rgba(168,85,247,0.05)', border: '1px solid rgba(168,85,247,0.18)' }}>ALL</motion.button>
          {tags.map(tag => <motion.button key={tag} whileTap={{ scale: 0.95 }} onClick={() => setActiveTag(activeTag === tag ? null : tag)} className="flex items-center gap-1 px-2 py-1 rounded-md cursor-pointer" style={{ ...mono, fontSize: '9px', color: activeTag === tag ? '#a855f7' : 'rgba(168,85,247,0.65)', background: activeTag === tag ? 'rgba(168,85,247,0.2)' : 'rgba(168,85,247,0.05)', border: '1px solid rgba(168,85,247,0.18)' }}><Tag className="w-2.5 h-2.5" />{tag}</motion.button>)}
        </div>
      )}

      <div className="flex-1 overflow-y-auto flex flex-col gap-2 pr-1">
        <AnimatePresence initial={false} mode="popLayout">
          {loading ? [0, 1, 2].map(index => <motion.div key={index} animate={{ opacity: [0.25, 0.55, 0.25] }} transition={{ duration: 1.2, repeat: Infinity, delay: index * 0.15 }} className="h-20 rounded-xl" style={{ background: 'rgba(168,85,247,0.08)', border: '1px solid rgba(168,85,247,0.12)' }} />) : visibleMemories.length === 0 ? (
            <div key="empty" className="rounded-xl p-4 text-center" style={{ background: 'rgba(168,85,247,0.05)', border: '1px solid rgba(168,85,247,0.12)' }}>
              <p style={{ ...raj, color: 'rgba(255,255,255,0.6)', fontSize: '13px' }}>No memories found.</p>
              <p style={{ ...mono, color: 'rgba(168,85,247,0.6)', fontSize: '9px' }}>USE + TO ADD ONE</p>
            </div>
          ) : visibleMemories.map(memory => (
            <motion.div key={memory.id} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -8 }} className="relative rounded-xl p-3 group" style={{ background: 'rgba(0,8,25,0.5)', border: '1px solid rgba(168,85,247,0.12)' }}>
              <div className="flex items-start justify-between gap-2 mb-1"><span style={{ ...raj, color: 'rgba(255,255,255,0.85)', fontSize: '13px' }}>{memory.title}</span><div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity"><button onClick={() => openEdit(memory)} className="cursor-pointer"><Edit className="w-3 h-3" style={{ color: '#a855f7' }} /></button><button onClick={() => void removeMemory(memory.id)} className="cursor-pointer"><Trash2 className="w-3 h-3" style={{ color: '#ef4444' }} /></button></div></div>
              <p className="line-clamp-3 mb-2" style={{ ...mono, color: 'rgba(255,255,255,0.42)', fontSize: '10px', lineHeight: 1.5 }}>{memory.content}</p>
              <div className="flex items-center justify-between gap-2"><div className="flex flex-wrap gap-1">{memory.tags.map(tag => <span key={tag} className="px-1.5 py-0.5 rounded" style={{ ...mono, color: '#a855f7', background: 'rgba(168,85,247,0.1)', fontSize: '8px' }}>{tag}</span>)}</div><span className="flex items-center gap-1 flex-shrink-0" style={{ ...mono, color: 'rgba(255,255,255,0.25)', fontSize: '9px' }}><Clock className="w-2.5 h-2.5" />{formatTime(memory.timestamp)}</span></div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      <AnimatePresence>
        {modal && <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-[250] flex items-center justify-center p-6" style={{ background: 'rgba(0,5,15,0.78)', backdropFilter: 'blur(8px)' }}>
          <motion.div initial={{ scale: 0.95, y: 12 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.95, y: 12 }} className="w-full max-w-md rounded-2xl p-5" style={{ background: 'rgba(0,10,25,0.96)', border: '1px solid rgba(168,85,247,0.3)' }}>
            <div className="flex items-center justify-between mb-4"><span style={{ ...orb, color: '#a855f7', fontSize: '13px' }}>{modal === 'create' ? 'ADD MEMORY' : 'EDIT MEMORY'}</span><button onClick={closeModal} className="cursor-pointer"><X className="w-4 h-4" style={{ color: 'rgba(255,255,255,0.55)' }} /></button></div>
            <div className="flex flex-col gap-3"><input value={form.title} onChange={event => setForm({ ...form, title: event.target.value })} placeholder="Memory title" className="rounded-lg px-3 py-2 outline-none" style={{ ...raj, background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(168,85,247,0.2)', color: 'white' }} /><textarea value={form.content} onChange={event => setForm({ ...form, content: event.target.value })} placeholder="What should JARVIS remember?" rows={4} className="rounded-lg px-3 py-2 outline-none resize-none" style={{ ...raj, background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(168,85,247,0.2)', color: 'white' }} /><input value={form.tags} onChange={event => setForm({ ...form, tags: event.target.value })} placeholder="Tags, separated by commas" className="rounded-lg px-3 py-2 outline-none" style={{ ...raj, background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(168,85,247,0.2)', color: 'white' }} /><label className="flex items-center gap-2" style={{ ...mono, color: 'rgba(255,255,255,0.6)', fontSize: '10px' }}><input type="checkbox" checked={form.synced} onChange={event => setForm({ ...form, synced: event.target.checked })} />SYNCED</label><button onClick={() => void saveMemory()} disabled={loading} className="rounded-lg py-2 cursor-pointer disabled:opacity-50" style={{ ...mono, background: 'rgba(168,85,247,0.2)', border: '1px solid rgba(168,85,247,0.45)', color: '#c084fc', fontSize: '10px' }}>{loading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : modal === 'create' ? 'CREATE MEMORY' : 'SAVE CHANGES'}</button></div>
          </motion.div>
        </motion.div>}
      </AnimatePresence>
    </div>
  );
}
